'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const installer=require('../.local/beta/install-dona.cjs'); // Our deployment entry, never the upstream installer.
const capsule=require('../.local/beta/dona-maintenance.json');
const {hash,classify,transaction,target,run}=installer;
const upstreamRoots={plugin:'payload/plugin',extension:'payload/extension',app:'overlay/app'};
async function fixture(t,kind='upstream'){
  const dir=await fs.mkdtemp(path.join(root,'.local','installer-test-'));
  t.after(async()=>{assert.equal(path.dirname(dir),path.join(root,'.local'));await fs.rm(dir,{recursive:true,force:true});});
  const targets={plugin:'plugins/quick-v',extension:'extensions/quick-v',app:'quick-v-runtime/code-v2/app'};
  for(const [name,sha] of Object.entries(capsule.baseline)){
    const [type,...parts]=name.split('/');
    const source=path.join(root,'.local/release',upstreamRoots[type],...parts);
    // Test fixtures use the statically extracted baseline, without executing it.
    const bytes=capsule.restore[name]?Buffer.from(capsule.restore[name].base64,'base64'):await fs.readFile(source);assert.equal(hash(bytes),sha,name);
    const file=path.join(dir,targets[type],...parts);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,bytes);
  }
  await fs.writeFile(path.join(dir,'plugins/quick-v/.quick-v-managed.json'),JSON.stringify({schema:1,owner:'sillydroid-quick-v',version:'0.6.5'}));
  await fs.mkdir(path.join(dir,'quick-v-state'));
  await fs.mkdir(path.join(dir,'chats'));
  await fs.writeFile(path.join(dir,'chats','private.txt'),'SYNTHETIC PRIVATE CHAT');
  await fs.writeFile(path.join(dir,'quick-v-state','private-config'),'SYNTHETIC PRIVATE CONFIG');
  if(kind==='dona'){
    const changes=Object.fromEntries(Object.entries(capsule.install).map(([name,item])=>[name,Buffer.from(item.base64,'base64')]));
    const expected=Object.fromEntries(Object.keys(changes).map(name=>[name,capsule.baseline[name]??null]));
    await transaction(dir,changes,expected);
  }
  return dir;
}
function deps(data){
  const downloads=[];let locks=0,spawns=0;
  const core={preflight:async()=>({data}),assertManaged:async()=>{},reusableRuntime:async()=>true,alive:()=>false,
    acquireLock:async()=>{locks++;return async()=>{locks--;};}};
  return {data,core,skipPlatform:true,report(){},downloads,get locks(){return locks;},get spawns(){return spawns;},
    download:async(spec)=>{downloads.push(spec.name);return spec.name==='dona-maintenance.json'?Buffer.from(JSON.stringify(capsule)):Buffer.from('// synthetic verified installer stub');},
    spawn:()=>{spawns++;return {status:0};}};
}
test('original 0.6.5 upgrades in place without downloading runtime or invoking full installer',async t=>{
  const data=await fixture(t);assert.equal(await classify(data,capsule),'upstream');
  const d=deps(data);assert.equal(await run('install',d),'dona');assert.equal(await classify(data,capsule),'dona');
  assert.equal(d.spawns,0);assert.equal(d.locks,0);assert.equal(d.downloads.length,2);
  assert.equal(await fs.readFile(path.join(data,'chats/private.txt'),'utf8'),'SYNTHETIC PRIVATE CHAT');
  assert.equal(await fs.readFile(path.join(data,'quick-v-state/private-config'),'utf8'),'SYNTHETIC PRIVATE CONFIG');
});
test('same version is a no-op and needs no installer download',async t=>{
  const data=await fixture(t,'dona');const d=deps(data);
  assert.equal(await run('install',d),'dona');assert.deepEqual(d.downloads,['dona-maintenance.json']);assert.equal(d.locks,0);
});
test('restore upstream removes only added dona modules and preserves user data',async t=>{
  const data=await fixture(t,'dona');const d=deps(data);
  assert.equal(await run('restore',d),'upstream');assert.equal(await classify(data,capsule),'upstream');
  for(const [name,item] of Object.entries(capsule.restore))if(item===null)await assert.rejects(fs.stat(await target(data,name)),{code:'ENOENT'});
  assert.equal(await fs.readFile(path.join(data,'quick-v-state/private-config'),'utf8'),'SYNTHETIC PRIVATE CONFIG');
});
test('injected partial failure rolls back exact previous bytes',async t=>{
  const data=await fixture(t);
  const changes=Object.fromEntries(Object.entries(capsule.install).map(([name,item])=>[name,Buffer.from(item.base64,'base64')]));
  const expected=Object.fromEntries(Object.keys(changes).map(name=>[name,capsule.baseline[name]??null]));
  await assert.rejects(transaction(data,changes,expected,{failAfter:4}),/已恢复/);
  assert.equal(await classify(data,capsule),'upstream');
});
test('modified installation fails closed',async t=>{
  const data=await fixture(t);await fs.appendFile(await target(data,'plugin/public/app.js'),'\n// local change');
  const d=deps(data);await assert.rejects(run('install',d),/本机修改/);assert.equal(d.downloads.length,1);assert.equal(d.locks,0);
});
test('live service blocks changes and releases the existing lock',async t=>{
  const data=await fixture(t);await fs.writeFile(path.join(data,'quick-v-state/process.json'),JSON.stringify({pid:123,startTicks:'1'}));
  const d=deps(data);d.core.alive=()=>true;
  await assert.rejects(run('install',d),/仍在运行/);assert.equal(d.locks,0);assert.equal(await classify(data,capsule),'upstream');
});
test('failed runtime integrity prevents any replacement',async t=>{
  const data=await fixture(t);const d=deps(data);d.core.reusableRuntime=async()=>false;
  await assert.rejects(run('install',d),/完整性/);assert.equal(await classify(data,capsule),'upstream');
});
test('unsafe paths and damaged capsules are rejected',async t=>{
  const data=await fixture(t);
  for(const name of ['app/../../private','plugin/../state','extension/C:\\private','unknown/x'])await assert.rejects(target(data,name));
  const bad=structuredClone(capsule);Object.values(bad.install)[0].sha256='0'.repeat(64);
  assert.throws(()=>installer.decodeChanges(bad,'install'),/校验失败/);
  await assert.rejects(installer.getBytes('http://example.com/x',{size:1,sha256:'0'.repeat(64)}),/HTTPS/);
});
test('fresh installs use only the checksum-verified full installer path',async t=>{
  const data=await fs.mkdtemp(path.join(root,'.local','installer-test-'));
  t.after(async()=>{assert.equal(path.dirname(data),path.join(root,'.local'));await fs.rm(data,{recursive:true,force:true});});
  const d=deps(data);assert.equal(await run('install',d),'installed');assert.equal(d.spawns,1);assert.equal(d.locks,0);
});
test('unsupported platform is rejected before network access',async()=>{
  if(process.platform==='linux'&&process.arch==='arm64')return;
  await assert.rejects(run('install',{download:()=>{throw Error('network must not run')}}),/安卓 ARM64/);
});
test('native Android and Linux ARM64 Node builds retain all original host requirements',()=>{
  for(const platform of ['android','linux'])assert.equal(installer.supportedPlatform({platform,arch:'arm64',hasToybox:true,nodeMajor:18}),true);
  for(const override of [{platform:'win32'},{arch:'x64'},{hasToybox:false},{nodeMajor:16}])
    assert.equal(installer.supportedPlatform({platform:'android',arch:'arm64',hasToybox:true,nodeMajor:18,...override}),false);
});
test('HTTPS download accepts only exact pinned bytes before use',async t=>{
  const https=require('node:https');const {EventEmitter}=require('node:events');const {Readable}=require('node:stream');
  const previous=https.get;t.after(()=>{https.get=previous;});
  const bytes=Buffer.from('synthetic release bytes');
  https.get=(_url,_options,callback)=>{
    const request=new EventEmitter();request.setTimeout=()=>request;request.destroy=e=>request.emit('error',e);
    process.nextTick(()=>{const response=Readable.from([bytes]);response.statusCode=200;response.headers={};callback(response);});
    return request;
  };
  assert.deepEqual(await installer.getBytes('https://github.com/test',{size:bytes.length,sha256:hash(bytes)}),bytes);
  await assert.rejects(installer.getBytes('https://github.com/test',{size:bytes.length,sha256:'0'.repeat(64)}),/SHA-256/);
});
