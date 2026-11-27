#!/usr/bin/env python3
"""Publish a verified prerelease using existing GitHub credentials, never logging tokens.

Prefer GH_TOKEN/GITHUB_TOKEN or the configured Git credential helper. Credentials
remain in process memory and are sent only to GitHub API/upload endpoints.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import prepare_beta as beta
from audit_release import audit

def token():
    value=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if value:return value
    # Use the same authentication as git push; do not expose it to model/tool output.
    env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'}
    result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env=env,cwd=ROOT,timeout=30)
    pairs=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    if result.returncode or not pairs.get('password'):raise RuntimeError('现有 GitHub 登录不能用于 Release API；未输出或保存凭据。请配置 GitHub CLI/GH_TOKEN 后重试此发布脚本。')
    return pairs['password']

class GitHub:
    def __init__(self,credential):self.credential=credential
    def request(self,method,url,body=None,raw=False):
        if not url.startswith(('https://api.github.com/','https://uploads.github.com/')):raise ValueError('Unapproved credential destination')
        headers={'Authorization':'Bearer '+self.credential,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'dona-QuickV-release'}
        if body is not None:
            data=body if raw else json.dumps(body,ensure_ascii=False).encode()
            headers['Content-Type']='application/octet-stream' if raw else 'application/json'
        else:data=None
        request=urllib.request.Request(url,data=data,headers=headers,method=method)
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):raise RuntimeError('Authenticated API redirect refused')
        try:
            with urllib.request.build_opener(NoRedirect).open(request,timeout=90) as response:
                content=response.read();return json.loads(content) if content else None
        except urllib.error.HTTPError as error:
            if error.code==404:return None
            raise RuntimeError('GitHub '+method+' 请求失败：HTTP '+str(error.code)) from None

def publish(output,preview=False):
    audit(output)
    if preview:print('Preview passed. No network mutation.');return
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():raise RuntimeError('请先提交工作区中的发布源码和固定版本导入文件。')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    api=GitHub(token());base='https://api.github.com/repos/'+beta.REPO
    repo=api.request('GET',base)
    if not repo or repo.get('visibility')!='public':raise RuntimeError('预期的公开仓库未确认。')
    branch=api.request('GET',base+'/git/ref/heads/codex/mobile-integration-065')
    if branch['object']['sha']!=head:raise RuntimeError('请先将当前提交推送到现有开发分支。')
    main=api.request('GET',base+'/git/ref/heads/main')['object']['sha']
    release=api.request('GET',base+'/releases/tags/'+beta.TAG)
    if release and not release.get('draft'):raise RuntimeError('该版本已发布；固定版本不覆盖，请使用新测试版本。')
    if release is None:
        drafts=api.request('GET',base+'/releases?per_page=100') or []
        release=next((r for r in drafts if r['tag_name']==beta.TAG and r['draft']),None)
    notes=(ROOT/'docs/release-notes.md').read_text(encoding='utf-8')
    if release is None:
        release=api.request('POST',base+'/releases',{'tag_name':beta.TAG,'target_commitish':head,'name':'快速 V 0.6.5 · dona美化 '+beta.VERSION+'（全新安装资源阻塞）',
                'body':notes,'draft':True,'prerelease':True,'make_latest':'false'})
    rid=release['id'];uploaded={asset['name']:asset for asset in release.get('assets',[])}
    names=[line.split('  ',1)[1] for line in (output/'SHA256SUMS').read_text().splitlines()]+['SHA256SUMS']
    for name in names:
        data=(output/name).read_bytes();digest='sha256:'+hashlib.sha256(data).hexdigest()
        if name in uploaded:
            if uploaded[name].get('digest')==digest:continue
            raise RuntimeError('草稿中有不同内容的同名资源，请人工审查后使用新版本，未覆盖现有文件。')
        asset=api.request('POST',release['upload_url'].split('{',1)[0]+'?name='+urllib.parse.quote(name),data,raw=True)
        if asset.get('digest')!=digest:raise RuntimeError('GitHub 上传摘要与本地不符，保留草稿未公开。')
        print('Uploaded and verified: '+name,flush=True)
    published=api.request('PATCH',base+'/releases/'+str(rid),{'draft':False,'prerelease':True,'make_latest':'false','body':notes})
    if api.request('GET',base+'/git/ref/heads/main')['object']['sha']!=main:raise RuntimeError('远程 main 发生变化；此脚本没有写入 main，请检查其他提交。')
    tag=api.request('GET',base+'/git/ref/tags/'+beta.TAG)
    if tag['object']['sha']!=head:raise RuntimeError('发布标签与待发布提交不一致。')
    print(json.dumps({'url':published['html_url'],'prerelease':published['prerelease'],'commit':head,'mainUnchanged':True},ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preview',action='store_true');args=parser.parse_args()
    try:publish(ROOT/'.local/beta',args.preview)
    except Exception as error:print('发布未完成：'+str(error),file=sys.stderr);raise SystemExit(1)
