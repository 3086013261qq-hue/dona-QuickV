#!/usr/bin/env node
/* dona Quick V deployment only. No authentication, forwarding or retry changes. */
'use strict';
const RELEASE = null; // Filled by tools/prepare_beta.py; never edit a published file.
const fs = require('node:fs');
const fsp = fs.promises;
const path = require('node:path');
const crypto = require('node:crypto');
const https = require('node:https');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const roots = { plugin: 'plugins/quick-v', extension: 'extensions/quick-v', app: 'quick-v-runtime/code-v2/app' };
const owner = 'sillydroid-quick-v';
function supportedPlatform({platform=process.platform,arch=process.arch,hasToybox=fs.existsSync('/system/bin/toybox'),nodeMajor=Number(process.versions.node.split('.')[0])}={}) {
  return ['android','linux'].includes(platform) && arch==='arm64' && hasToybox && nodeMajor>=18;
}

async function regular(file) {
  const st = await fsp.lstat(file);
  if (!st.isFile() || st.isSymbolicLink()) throw new Error('文件类型异常，已停止。');
  return st;
}
async function target(data, name) {
  const parts = name.split('/');
  const root = roots[parts.shift()];
  if (!root || !parts.length || parts.some(p => !p || p === '.' || p === '..' || /[\\:\x00-\x1f]/.test(p))) throw new Error('资源路径异常。');
  const result = path.join(data, root, ...parts);
  if (!result.startsWith(data + path.sep)) throw new Error('资源路径超出安装目录。');
  let parent = data;
  for (const part of path.relative(data, path.dirname(result)).split(path.sep)) {
    parent = path.join(parent, part);
    const st = await fsp.lstat(parent);
    if (!st.isDirectory() || st.isSymbolicLink()) throw new Error('安装目录包含异常链接。');
  }
  return result;
}
async function readDigest(file) {
  try { if ((await regular(file)).size > 16 * 1024 * 1024) throw new Error('静态文件大小超出安装清单范围。'); return hash(await fsp.readFile(file)); }
  catch (e) { if (e.code === 'ENOENT') return null; throw e; }
}
function getBytes(url, expected, hops = 0) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password || hops > 5) return reject(new Error('下载地址必须为 HTTPS。'));
    const req = https.get(parsed, { headers: { 'User-Agent': 'dona-QuickV-installer', Accept: 'application/octet-stream' } }, res => {
      if ([301,302,303,307,308].includes(res.statusCode)) {
        res.resume();
        if (!res.headers.location) return reject(new Error('下载重定向无效。'));
        getBytes(new URL(res.headers.location, parsed).href, expected, hops + 1).then(resolve, reject);return;
      }
      if (res.statusCode !== 200) { res.resume(); return reject(new Error('下载失败（HTTP ' + res.statusCode + '）。请检查网络或 Release 是否已发布。')); }
      const chunks = [];let total = 0;
      res.on('data', chunk => {
        total += chunk.length;
        if (total > expected.size) res.destroy(new Error('下载大小超过版本清单，已拒绝。'));
        else chunks.push(chunk);
      });
      res.on('error', reject);
      res.on('aborted', () => reject(new Error('下载中断，原安装未改变。')));
      res.on('end', () => {
        const bytes = Buffer.concat(chunks);
        if (bytes.length !== expected.size || hash(bytes) !== expected.sha256) reject(new Error('SHA-256 或大小校验失败，未执行下载内容。'));
        else resolve(bytes);
      });
    });
    req.setTimeout(30000, () => req.destroy(new Error('下载超时，请稍后重试。')));
    req.on('error', reject);
  });
}
async function download(spec, report = console.log) {
  report('下载并校验 ' + spec.name + '…');
  return getBytes(RELEASE.baseUrl + spec.name, spec);
}
async function marker(data) {
  try {
    const file = path.join(data, 'plugins/quick-v/.quick-v-managed.json');
    if ((await regular(file)).size > 2048) throw new Error();
    const value = JSON.parse(await fsp.readFile(file, 'utf8'));
    if (value.owner !== owner || value.schema !== 1) throw new Error();
    return value.version;
  } catch (e) { if (e.code === 'ENOENT') return null; throw new Error('原版安装标记异常，未修改安装。'); }
}
async function classify(data, capsule) {
  const version = await marker(data);
  if (version === null) return 'missing';
  if (version !== '0.6.5') return 'other';
  let original = true, installed = true;
  for (const [name, baseline] of Object.entries(capsule.baseline)) {
    const actual = await readDigest(await target(data, name));
    original &&= actual === baseline;
    installed &&= actual === (Object.hasOwn(capsule.install, name) ? capsule.install[name].sha256 : baseline);
  }
  for (const [name, item] of Object.entries(capsule.install)) {
    if (Object.hasOwn(capsule.baseline, name)) continue;
    const actual = await readDigest(await target(data, name));
    original &&= actual === null;
    installed &&= actual === item.sha256;
  }
  return original ? 'upstream' : installed ? 'dona' : 'modified';
}
function decodeChanges(capsule, mode) {
  if (capsule.schema !== 1 || capsule.version !== RELEASE.version || !capsule.baseline || !capsule.install || !capsule.restore) throw new Error('安装清单版本不符。');
  const source = mode === 'restore' ? capsule.restore : capsule.install;
  const changes = {};
  for (const [name, item] of Object.entries(source)) {
    if (!Object.hasOwn(capsule.install, name) || !Object.hasOwn(capsule.restore, name)) throw new Error('还原清单边界不符。');
    if (item === null) changes[name] = null;
    else {
      const bytes = Buffer.from(item.base64, 'base64');
      if (bytes.length !== item.size || hash(bytes) !== item.sha256) throw new Error('内置文件校验失败。');
      changes[name] = bytes;
    }
  }
  return changes;
}
async function assertStopped(data, core) {
  for (const name of ['process.json', 'guest-process.json']) {
    const file = path.join(data, 'quick-v-state', name);
    let raw;
    try { if ((await regular(file)).size > 8192) throw new Error(); raw = JSON.parse(await fsp.readFile(file, 'utf8')); }
    catch (e) { if (e.code === 'ENOENT') continue; throw new Error('原版进程记录异常，请保留现场检查。'); }
    const entries = name === 'process.json' ? [raw] : [raw.watchdog, raw.server];
    if (name === 'guest-process.json') {
      const valid = item => item && Number.isSafeInteger(item.pid) && item.pid > 1 && typeof item.startTicks === 'string' && /^\d+$/.test(item.startTicks);
      if (raw.version !== 1 || !valid(raw.watchdog) || (raw.server !== null && !valid(raw.server))) throw new Error('原版子进程记录异常，请保留现场检查。');
    }
    if (entries.some(item => item && core.alive(item))) throw new Error('快速 V 仍在运行。请先在原面板停止服务，再执行同一命令。');
  }
}
async function transaction(data, changes, expected, { failAfter = -1 } = {}) {
  // Back up only the exact static files touched, in memory; never enumerate user data.
  const rows = [];
  for (const [name, bytes] of Object.entries(changes)) {
    const file = await target(data, name);
    const actual = await readDigest(file);
    if (actual !== expected[name]) throw new Error('安装文件在操作期间发生变化，已停止。');
    rows.push({ file, bytes, previous: actual === null ? null : await fsp.readFile(file), mode: actual === null ? 0o600 : (await regular(file)).mode & 0o777 });
  }
  const done = [];
  async function write(row, bytes) {
    if (bytes === null) { try { await fsp.unlink(row.file); } catch(e) { if(e.code !== 'ENOENT') throw e; } return; }
    const temp = row.file + '.dona-' + crypto.randomBytes(8).toString('hex') + '.tmp';
    try {
      await fsp.writeFile(temp, bytes, { flag: 'wx', mode: row.mode });
      await fsp.rename(temp, row.file);
    } finally { await fsp.unlink(temp).catch(e => { if (e.code !== 'ENOENT') throw e; }); }
  }
  try {
    for (const row of rows) {
      await write(row, row.bytes);done.push(row);
      if (done.length === failAfter) throw new Error('TEST_INJECTED_FAILURE');
    }
  } catch (e) {
    let failed = false;
    for (const row of done.reverse()) { try { await write(row, row.previous); } catch { failed = true; } }
    if (failed) throw new Error('回滚未完全成功，请勿重启快速 V；保留当前文件并使用已核验安装器修复。');
    throw new Error('操作失败，已恢复本次更改前的文件：' + e.message);
  }
}
async function run(mode = 'install', deps = {}) {
  if (!['install','status','restore'].includes(mode)) throw new Error('只支持 install、status、restore。');
  if (!RELEASE) throw new Error('请使用 Release 中已生成的安装入口。');
  const report = deps.report || console.log;
  if (!deps.skipPlatform && !supportedPlatform()) throw new Error('请在安卓 ARM64 的 SillyDroid → 设置 → 内置终端使用 Node.js 18+ 运行。');
  const dataInput = deps.data || process.env.APP_DATA_ROOT || process.env.TAVERN_DATA_ROOT;
  const server = process.env.SERVER_DIR || process.env.TAVERN_SERVER_DIR;
  if (!dataInput || !path.isAbsolute(dataInput) || (!deps.skipPlatform && !server)) throw new Error('未找到 SillyDroid 内置终端环境。');
  const data = await fsp.realpath(dataInput);
  report('快速 V 0.6.5 · dona美化 ' + RELEASE.version);
  const fetch = deps.download || download;
  const capsule = JSON.parse((await fetch(RELEASE.capsule, report)).toString('utf8'));
  const changes = decodeChanges(capsule, mode);
  let kind = await classify(data, capsule);
  report('当前状态：' + ({missing:'未安装',upstream:'原版 0.6.5',dona:'当前 dona 测试版本',other:'其他原版版本',modified:'文件存在额外修改，无法直接替换'}[kind]));
  if (mode === 'status') return kind;
  if ((kind === 'dona' && mode === 'install') || (kind === 'upstream' && mode === 'restore')) { report('当前文件已是目标版本，无需重复安装。');return kind; }
  if (kind === 'modified') throw new Error('为保留本机修改已停止。请先用已核验原版 0.6.5 安装器修复，然后重试。');
  if (mode === 'restore' && kind !== 'dona') throw new Error('仅能将本测试版恢复为原版 0.6.5。未删除任何用户数据。');
  const installer = await fetch(RELEASE.installer, report);
  const dir = await fsp.mkdtemp(path.join(os.tmpdir(), 'dona-qv-'));
  const file = path.join(dir, 'installer.cjs');
  try {
    await fsp.writeFile(file, installer, { flag: 'wx', mode: 0o600 });
    if (kind === 'missing' || kind === 'other') {
      if (!RELEASE.freshInstall?.ready) report('提示：本测试版的原作者外部运行资源在开发环境尚未获取成功。全新安装必须下载并校验这些资源；如出现 HTTP 403，请向原作者获取可用正式下载渠道，不能跳过校验。');
      report('进入原版完整安装流程，保留环境检测、资源校验、运行环境复用和失败回滚。');
      const result = (deps.spawn || spawnSync)(process.execPath, [file], { stdio:'inherit', shell:false });
      if (result.error || result.status !== 0) throw new Error('完整安装未完成。请按上方原版提示处理；不会绕过下载或访问限制。');
      return 'installed';
    }
    const core = deps.core || require(file);
    const ctx = deps.context || await core.preflight();
    if (await fsp.realpath(ctx.data) !== data) throw new Error('安装环境目录不一致。');
    for (const relative of ['plugins/quick-v','extensions/quick-v','quick-v-runtime','quick-v-runtime/code-v2']) await core.assertManaged(path.join(data,relative));
    if (!await core.reusableRuntime(data, capsule.runtime)) throw new Error('原版运行环境完整性校验未通过，请使用完整安装器修复。');
    const stateDir = path.join(data,'quick-v-state');
    const stateStat = await fsp.lstat(stateDir);
    if (!stateStat.isDirectory() || stateStat.isSymbolicLink()) throw new Error('原版状态目录异常。');
    await fsp.chmod(stateDir, 0o700);
    const unlock = await core.acquireLock(stateDir);
    try {
      await assertStopped(data, core);
      if (await classify(data,capsule) !== kind) throw new Error('安装文件已变化，请重试。');
      const expected = {};
      for (const name of Object.keys(changes)) expected[name] = mode === 'restore' ? capsule.install[name].sha256 : capsule.baseline[name] ?? null;
      report(mode === 'restore' ? '正在恢复原版文件；聊天、凭据与配置保持原样…' : '现有 0.6.5 与运行环境校验通过，正在安装美化和播报适配；不重新下载运行环境与 Python 依赖…');
      await transaction(data, changes, expected);
      report('完成。请重启 SillyDroid 酒馆服务。' + (mode === 'restore' ? '可在酒馆助手中单独关闭或删除播报脚本。' : '播报脚本请另行导入酒馆助手。'));
    } finally { await unlock(); }
    return mode === 'restore' ? 'upstream' : 'dona';
  } finally {
    // Only the single private directory created above can be removed.
    if (path.dirname(dir) !== path.resolve(os.tmpdir()) || !path.basename(dir).startsWith('dona-qv-')) throw new Error('临时目录边界异常。');
    await fsp.rm(dir, {recursive:true,force:true});
  }
}
if (require.main === module) {
  process.umask(0o077);
  run(process.argv[2] || 'install').catch(e => { console.error('未完成：' + e.message);process.exitCode=1; });
}
module.exports={hash,getBytes,target,marker,classify,decodeChanges,transaction,run,assertStopped,supportedPlatform};
