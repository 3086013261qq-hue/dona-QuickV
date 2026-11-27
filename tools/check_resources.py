#!/usr/bin/env python3
"""Check only pinned author resources. No execution, credentials, mirrors or access bypass."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin,urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'frontend/tools'))
from build_panel import load_release,EXPECTED
AUTHOR_INSTALLER='https://vertex-local-download-20261014.yuanfuyuan929.chatgpt.site/sillydroid/install-0.6.5.cjs'

def resources(release):
    return [dict(kind='author-installer',url=AUTHOR_INSTALLER,size=Path(ROOT/'install-0.6.5.cjs').stat().st_size,sha256=EXPECTED),
        *[dict(kind=kind,url=urljoin(release['baseUrl'],x['url']),size=x['size'],sha256=x['sha256'])
          for kind,items in [('runtime-apk-part',release['apk']['chunks']),('code-bundle-part',release['codeBundle']['chunks'])] for x in items],
        dict(kind='runtime-source',url=urljoin(release['baseUrl'],release['runtimeSource']['url']),size=release['runtimeSource']['size'],sha256=release['runtimeSource']['sha256'])]

def check(item,cache,download=False):
    parsed=urlsplit(item['url'])
    if parsed.scheme!='https' or parsed.hostname!='vertex-local-download-20261014.yuanfuyuan929.chatgpt.site':raise ValueError('Unreviewed source')
    file=cache/Path(parsed.path).name
    result={**item,'state':'missing'}
    if file.exists() and file.stat().st_size==item['size'] and hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']:
        return result|{'state':'verified-cache'}
    try:
        # Normal GET, no cookies, alternate hosts, anti-bot headers or access workarounds.
        with urllib.request.urlopen(item['url'],timeout=30) as response:
            result.update(http=response.status)
            if not download:
                response.read(1)
                return result|{'state':'reachable-unverified'}
            cache.mkdir(parents=True,exist_ok=True)
            temp=file.with_suffix(file.suffix+'.part')
            h=hashlib.sha256();total=0
            try:
                with temp.open('wb') as stream:
                    while chunk:=response.read(1024*1024):
                        total+=len(chunk)
                        if total>item['size']:raise ValueError('Resource exceeds pinned size')
                        h.update(chunk);stream.write(chunk)
                if total!=item['size'] or h.hexdigest()!=item['sha256']:raise ValueError('Size or SHA-256 mismatch')
                temp.replace(file)
                return result|{'state':'verified-download'}
            finally:
                if temp.exists():temp.unlink()
    except urllib.error.HTTPError as error:
        return result|{'state':'unavailable','http':error.code}
    except (OSError,ValueError) as error:
        return result|{'state':'unavailable','error':type(error).__name__}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--download',action='store_true');parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    _,release=load_release(ROOT/'install-0.6.5.cjs')
    items=resources(release)
    if args.render_only:
        values=json.loads((ROOT/'docs/resource-status.json').read_text(encoding='utf-8'))['resources']
    else:
        with ThreadPoolExecutor(max_workers=3) as pool:
            values=list(pool.map(lambda item:check(item,ROOT/'.local/upstream-downloads',args.download),items))
    required=[x for x in values if x['kind'] in ('runtime-apk-part','code-bundle-part')]
    report={'schema':1,'checkedDate':'2026-11-27','freshInstallReady':all(x['state'].startswith('verified-') for x in required),
            'runtimeApk':{k:release['apk'][k] for k in ['filename','size','sha256']},
            'codeBundle':{k:release['codeBundle'][k] for k in ['size','sha256','revision','unpackedSize']},
            'apkInternalAssets':release['assets'],'resources':values,
            'alternateOfficialSource':'No byte-compatible alternative confirmed. PC upstream has no Releases; SillyDroid host assets are not this Quick V Python runtime.'}
    output=ROOT/'docs/resource-status.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 全新安装资源核查 / 2026-11-27','',
       '**当前：资源未齐，全新安装阻塞。不能将增量升级通过视为只有 SillyDroid 的手机已可完整安装。**','',
       '用户提供的正式发布地址：['+AUTHOR_INSTALLER+']('+AUTHOR_INSTALLER+')。从开发环境使用普通 HTTPS GET，不带 Cookie、不伪装来源，返回 HTTP 403/连接错误。这是本次开发端检查结果，不断言所有手机网络均不可访问。未绕过访问限制，也未执行任何原始安装器或下载内容。','',
       '## 必需资源与获取方式','',
       '需要原作者恢复以下正式下载资源，或提供对应相同 SHA-256 的正式备用渠道。只有文本安装器不足以提供 Python 环境。','',
       '| 资源 | 总字节数 | 固定 SHA-256 |','|---|---:|---|',
       f'| vertex-local.apk（6 段合并） | {release["apk"]["size"]} | `{release["apk"]["sha256"]}` |',
       f'| Quick V codeBundle（3 段合并） | {release["codeBundle"]["size"]} | `{release["codeBundle"]["sha256"]}` |','',
       '实际缺失文件及原作者地址（每段还须独立核验）：','',
       '| 文件/用途 | 字节数 | SHA-256 | 本次结果 |','|---|---:|---|---|']
    for item in values:
        label=Path(urlsplit(item['url']).path).name
        result=('HTTP '+str(item['http'])) if 'http' in item else item['state']
        lines.append(f'| [{label}]({item["url"]}) · {item["kind"]} | {item["size"]} | `{item["sha256"]}` | {result} |')
    lines += ['','`runtime-source-1.8.zip` 是原版清单列出的复现/源码资源，不是全新安装时必需执行的安装脚本；当前也未取得。原始 CJS 仅从用户已提供的本地副本静态核验，不重新公开上传。','',
       '## APK 内必须存在的组件','',
       '运行 APK 包含 Python 3.12 的 ARM64 rootfs、原生 proot/loader/共享库、旧 app-v1.8 及其 manifest；新 codeBundle 提供 code-v2/app 和 site 依赖，再叠加已验证内嵌 appOverlay。原始清单对 APK 内组件也逐项规定大小和摘要：','',
       '| APK 内部路径 | 字节数 | SHA-256 |','|---|---:|---|']
    for name,item in release['assets'].items():lines.append(f'| `{name}` | {item["size"]} | `{item["sha256"]}` |')
    lines += ['','## 正式备用来源与兼容性核查','',
       '- [PC 上游](https://github.com/bad-woman/vertex2openai) 当前没有 GitHub Releases；已检查 README 与仓库树，没有核实到该 Quick V ARM64 Python 运行包。','- [SillyDroid 官方仓库](https://github.com/jialmaster/SillyDroid) 的 Release 是酒馆宿主/Node 环境，不是上述 Quick V 专用 Python 包；不能不经摘要和启动兼容审查就替换。','- 原版原生组件声明提供 Termux 正式包 URL 和许可证，但零散 deb 不能替代已固定的 Python rootfs、代码 site 和安装布局；本次不重建或重新分发这些第三方文件。','- 原作者手机二改身份未从仓库署名核实，不按域名用户名推测其他下载站。未找到可证明由手机原作者提供、且满足这些固定摘要的备用渠道。','',
       '获取后应运行 `python tools/check_resources.py --download`，核对全部段、合并总包及内层资源，再做安卓 ARM64 真机全新安装。大小不符、SHA 不符、未知镜像、登录页响应都拒绝。不能通过删除校验或伪造环境标记让测试通过。资源和实际安装兼容性未验证前，freshInstallReady 始终为 false。','',
       '本测试版包含完整原安装流程入口和升级/恢复工具，但**不包含这些第三方运行资源，不是离线完整运行包，当前不构成已验收的全新安装交付**。']
    (ROOT/'docs/resources.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'freshInstallReady':report['freshInstallReady'],'resources':[{k:x[k] for k in ['kind','url','state','http'] if k in x} for x in values]},ensure_ascii=False,indent=2))
    return 0 if report['freshInstallReady'] else 2

if __name__=='__main__':raise SystemExit(main())
