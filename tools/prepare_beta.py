#!/usr/bin/env python3
"""Build release-only artifacts and fixed-version helper imports; never execute upstream."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_release as build

VERSION='0.1.0-beta.2'
REPO='3086013261qq-hue/dona-QuickV'
TAG='v'+VERSION
BASE=f'https://github.com/{REPO}/releases/download/{TAG}/'
CDN=f'https://cdn.jsdelivr.net/gh/{REPO}@{TAG}/'

def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(data):return dict(size=len(data),sha256=sha(data),base64=base64.b64encode(data).decode())
def spec(path):return dict(name=path.name,size=path.stat().st_size,sha256=sha(path.read_bytes()))
def write_json(path,data):path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())

def command(url,digest,size,mode='install'):
    # The first remote byte is never executed until its independently pinned digest matches.
    # SillyDroid supplies TERMUX_CURL_BIN; toybox is required by the upstream installer.
    # A private mktemp directory and independently pinned SHA precede any Node execution.
    return ('(umask 077; dona_tmp=$(/system/bin/toybox mktemp -d) && '
            '"$TERMUX_CURL_BIN" --fail --location --proto "=https" --proto-redir "=https" --connect-timeout 15 --max-time 120 --max-filesize '+str(size)+' -o "$dona_tmp/install.cjs" '+shlex.quote(url)+
            ' && printf "%s  %s\\n" '+shlex.quote(digest)+' "$dona_tmp/install.cjs" | /system/bin/toybox sha256sum -c - && node "$dona_tmp/install.cjs" '+mode+')')

def prepare(installer,output):
    output.mkdir(parents=True,exist_ok=True)
    _,original=build.load_release(installer)
    # Existing baseline builder remains untouched; preserve its business files and tests.
    built,_=build.build(installer,ROOT/'.local/release')
    original_overlay=build.overlay_files(original)
    updated_overlay=build.overlay_files(built)
    baseline={}
    changes={}
    restore={}
    for name,meta in original['files'].items():
        if name.startswith(('plugin/','extension/')):baseline[name]=meta['sha256']
    for name,(data,_) in original_overlay.items():
        if name.startswith('app/'):baseline[name]=sha(data)
    for name,meta in built['files'].items():
        if not name.startswith(('plugin/','extension/')):continue
        if name not in original['files'] or original['files'][name]['sha256']!=meta['sha256']:
            changes[name]=encoded(build.verified(meta))
            restore[name]=encoded(build.verified(original['files'][name])) if name in original['files'] else None
    for name,(data,_) in updated_overlay.items():
        if not name.startswith('app/'):continue
        if name not in original_overlay or data!=original_overlay[name][0]:
            changes[name]=encoded(data)
            restore[name]=encoded(original_overlay[name][0]) if name in original_overlay else None
    capsule=dict(schema=1,version=VERSION,upstreamVersion='0.6.5',baseline=baseline,install=changes,restore=restore,
                 runtime={key:original[key] for key in ['apk','assets','reuseCoreFiles','reuseLinks']})
    write_json(output/'dona-maintenance.json',capsule)
    old=ROOT/'.local/release'/f'install-quick-v-0.6.5-dona-{build.REVISION}.cjs'
    cjs=output/f'install-quick-v-0.6.5-dona-{VERSION}.cjs'
    shutil.copyfile(old,cjs)
    metadata=dict(version=VERSION,repository=REPO,baseUrl=BASE,installer=spec(cjs),capsule=spec(output/'dona-maintenance.json'))
    if (ROOT/'docs/resource-status.json').exists():
        status=json.loads((ROOT/'docs/resource-status.json').read_text(encoding='utf-8'))
        metadata['freshInstall']={'ready':status['freshInstallReady'],'checkedDate':status['checkedDate'],
             'status':'resources-verified' if status['freshInstallReady'] else 'upstream-resources-unavailable-in-development-environment'}
    template=(ROOT/'delivery/install.cjs').read_text(encoding='utf-8')
    if template.count('const RELEASE = null;')!=1:raise ValueError('Bootstrap template contract changed')
    bootstrap=template.replace('const RELEASE = null;','const RELEASE = '+json.dumps(metadata,ensure_ascii=False,separators=(',',':'))+';')
    boot=output/'install-dona.cjs';boot.write_bytes(bootstrap.encode())
    write_json(output/'version.json',metadata|{'bootstrap':spec(boot),'upstreamInstallerSha256':build.digest(Path(installer).read_bytes()),
          'publicDistribution':{'authorizedBy':'repository owner confirmation in development chat on 2026-11-27','scope':'modified CJS and delivery ZIP; runtime dependencies remain on upstream resources'}})
    source=ROOT/'frontend/broadcast/dona-broadcast.js'
    source_bytes=source.read_bytes().replace(b'\r\n',b'\n') # CDN serves the Git LF blob, independent of local autocrlf.
    (output/'dona-broadcast.js').write_bytes(source_bytes)
    loader=f'''/* dona快V · 战术播报 {VERSION}; fixed-version, one fetch per script activation. */
(async () => {{
  const stop = new AbortController();
  window.addEventListener('pagehide', () => stop.abort(), {{ once: true }});
  let blob;
  try {{
    const response = await fetch({json.dumps(CDN+'frontend/broadcast/dona-broadcast.js')}, {{ signal: stop.signal, credentials: 'omit', redirect: 'error' }});
    if (!response.ok) throw new Error('脚本下载失败：HTTP ' + response.status);
    const chunks = []; let size = 0;
    const reader = response.body.getReader();
    while (true) {{
      const {{ value: chunk, done }} = await reader.read();
      if (done) break;
      size += chunk.length;
      if (size > {len(source_bytes)}) throw new Error('脚本大小不符');
      chunks.push(chunk);
    }}
    const bytes = new Uint8Array(size); let offset = 0;
    for (const chunk of chunks) {{ bytes.set(chunk, offset); offset += chunk.length; }}
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), n => n.toString(16).padStart(2, '0')).join('');
    if (size !== {len(source_bytes)} || digest !== {json.dumps(sha(source_bytes))}) throw new Error('脚本 SHA-256 校验失败');
    if (stop.signal.aborted) return;
    blob = URL.createObjectURL(new Blob([bytes], {{ type: 'text/javascript' }}));
    await import(blob);
  }} catch (error) {{
    if (!stop.signal.aborted) console.error('[dona快V] ' + error.message);
  }} finally {{ if (blob) URL.revokeObjectURL(blob); }}
}})();
'''
    cloud=ROOT/f'frontend/broadcast/cloud/{TAG}.js';cloud.parent.mkdir(parents=True,exist_ok=True);cloud.write_bytes(loader.encode())
    item=dict(type='script',enabled=False,name='dona快V · 战术播报',id='57c6ad80-711a-4d83-96a0-8d54fe7da465',
              content="import '"+CDN+f'frontend/broadcast/cloud/{TAG}.js'+"';",info=f'dona {VERSION}；Quick V 0.6.5；启用时一次下载并校验播报源码，不轮询更新。关闭/删除脚本可卸载。',
              button={'enabled':False,'buttons':[]},data={},export_with={'data':False,'button':False})
    imports=ROOT/f'frontend/broadcast/imports/{TAG}.json';imports.parent.mkdir(parents=True,exist_ok=True);write_json(imports,item)
    shutil.copyfile(imports,output/'dona-broadcast.tavern-helper.json')
    shutil.copyfile(cloud,output/'dona-cloud-loader.js')
    commands={mode:command(BASE+boot.name,sha(boot.read_bytes()),boot.stat().st_size,mode) for mode in ['install','status','restore']}
    write_json(output/'commands.json',commands)
    template=ROOT/'docs/README.template.md'
    if template.exists():
        readme=template.read_text(encoding='utf-8')
        for mode,value in commands.items():readme=readme.replace('{{'+mode.upper()+'_COMMAND}}',value)
        (ROOT/'README.md').write_bytes(readme.encode())
    for name in ['installation.md','third-party-notices.md','testing.md','release-notes.md','resources.md','resource-status.json']:
        if (ROOT/'docs'/name).exists():shutil.copyfile(ROOT/'docs'/name,output/name)
    shutil.copyfile(ROOT/'.local/release/UPSTREAM-LICENSE',output/'UPSTREAM-LICENSE')
    files=[cjs.name,'install-dona.cjs','dona-maintenance.json','version.json','commands.json','dona-broadcast.js',
           'dona-broadcast.tavern-helper.json','dona-cloud-loader.js','UPSTREAM-LICENSE','installation.md','third-party-notices.md','testing.md','release-notes.md','resources.md','resource-status.json']
    files=[name for name in files if (output/name).is_file()]
    archive=output/f'quick-v-0.6.5-dona-{VERSION}.zip'
    with zipfile.ZipFile(archive,'w') as z:
        for name in files:
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,(output/name).read_bytes())
    # SHA256SUMS covers ZIP too; ZIP contents have their hashes in version/embedded manifests.
    (output/'SHA256SUMS').write_bytes(''.join(f'{sha((output/name).read_bytes())}  {name}\n' for name in [*files,archive.name]).encode())
    print(json.dumps({'version':VERSION,'output':str(output.resolve()),'installer':spec(boot),'assets':len(files)+2},ensure_ascii=False,indent=2))
    return metadata,commands

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer',type=Path,default=ROOT/'install-0.6.5.cjs')
    parser.add_argument('--output',type=Path,default=ROOT/'.local/beta')
    args=parser.parse_args();prepare(args.installer,args.output)
