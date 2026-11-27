#!/usr/bin/env python3
"""Audit reachable Git text, authorized package resources and release SHA256SUMS."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_release as build
import prepare_beta as beta

SIGNATURES=[rb'AIza[0-9A-Za-z_-]{35}',rb'gh[pousr]_[0-9A-Za-z]{20,}',rb'github_pat_[0-9A-Za-z_]{30,}',
            rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'sk-(?:proj-|ant-)?[0-9A-Za-z_-]{30,}']

def scan(data,upstream_static_client=False):
    for index,pattern in enumerate(SIGNATURES):
        if re.search(pattern,data):
            # This exact, unchanged upstream module contains Google's console frontend
            # client identifier in BATCH_GRAPHQL_URL. It is not a user's Google key or
            # cookie. Never allow other blobs, locations or modified contents.
            if upstream_static_client and index==0 and hashlib.sha256(data).hexdigest()=='723165ab6ca341d48c95e7d26a6bfffe6680c925718fe87dec151d5a45438b6e':continue
            raise ValueError('Potential credential signature: publication blocked; no matched value printed')

def audit(output=ROOT/'.local/beta'):
    policy=json.loads((ROOT/'release-policy.json').read_text(encoding='utf-8'))
    if policy.get('public_distribution_authorized') is not True or policy.get('upstream_runtime_redistribution') is not False:raise ValueError('Public distribution authorization not recorded')
    git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT)
    commits=git('rev-list','HEAD').decode().splitlines()
    blobs=set();paths=set()
    for commit in commits:
        for row in git('ls-tree','-r',commit).decode().splitlines():
            meta,name=row.split('\t',1);oid=meta.split()[2]
            paths.add(name);blobs.add(oid)
    for name in paths:
        if name=='install-0.6.5.cjs' or name.startswith(('.local/','.env','downloads/')) or name.endswith(('.dpapi','.apk','.tar.gz')):
            raise ValueError('Private or raw installer path in Git history')
    for oid in blobs:scan(git('cat-file','blob',oid))
    expected={}
    for line in (output/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1)
        if Path(name).name!=name or name in expected:raise ValueError('Unsafe asset name')
        data=(output/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Release checksum mismatch: '+name)
        scan(data);expected[name]=digest
    raw,original=build.load_release(ROOT/'install-0.6.5.cjs')
    cjs=output/f'install-quick-v-0.6.5-dona-{beta.VERSION}.cjs'
    text=cjs.read_text(encoding='utf-8');release,_=json.JSONDecoder().raw_decode(text.split('const RELEASE = ',1)[1])
    if cjs.read_bytes()==(ROOT/'install-0.6.5.cjs').read_bytes():raise ValueError('Raw upstream installer cannot be published')
    for key in ['apk','assets','runtimeSource','reuseCoreFiles','reuseLinks']:
        if release[key]!=original[key]:raise ValueError('Unreviewed runtime dependency change')
    for name,meta in release['files'].items():
        data=build.verified(meta);scan(data)
        data.decode('utf-8') # Embedded assets must be source and notices, not third-party binaries.
    for name,(data,_) in build.overlay_files(release).items():scan(data,upstream_static_client=name=='app/cookie_auth.py');data.decode('utf-8')
    capsule=json.loads((output/'dona-maintenance.json').read_text())
    for mode in ['install','restore']:
        for name,item in capsule[mode].items():
            if item is None:continue
            if not name.startswith(('plugin/','extension/','app/')):raise ValueError('Unreviewed maintenance target')
            data=base64.b64decode(item['base64'],validate=True);scan(data);data.decode('utf-8')
            if len(data)!=item['size'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Capsule integrity failure')
    archive=output/f'quick-v-0.6.5-dona-{beta.VERSION}.zip'
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise ValueError('Delivery ZIP invalid')
        for name in z.namelist():
            if Path(name).name!=name or name not in expected or name.endswith('.zip'):raise ValueError('Unexpected ZIP member')
            if hashlib.sha256(z.read(name)).hexdigest()!=expected[name]:raise ValueError('ZIP checksum mismatch')
    result={'commits':len(commits),'paths':len(paths),'gitBlobs':len(blobs),'assets':len(expected)+1,
            'rawInstallerPublished':False,'runtimeBinariesRedistributed':False,'userCredentialSignaturesFound':False,
            'unchangedUpstreamGoogleConsoleClientIdentifierModules':1}
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':audit()
