import hashlib
import json
from pathlib import Path
import subprocess
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/beta'

class BetaTests(unittest.TestCase):
    def test_pinned_bootstrap_and_commands(self):
        version=json.loads((OUT/'version.json').read_text(encoding='utf-8'))
        bootstrap=(OUT/'install-dona.cjs').read_bytes()
        self.assertEqual(hashlib.sha256(bootstrap).hexdigest(),version['bootstrap']['sha256'])
        commands=json.loads((OUT/'commands.json').read_text())
        readme=(ROOT/'README.md').read_text(encoding='utf-8')
        for mode,command in commands.items():
            self.assertIn('@v0.1.0-beta.2',json.loads((ROOT/'frontend/broadcast/imports/v0.1.0-beta.2.json').read_text(encoding='utf-8'))['content'])
            self.assertIn(version['bootstrap']['sha256'],command)
            self.assertLess(command.index('sha256sum -c -'),command.index('&& node '))
            self.assertIn('releases/download/v0.1.0-beta.2/install-dona.cjs',command)
            self.assertIn(command,readme)
            self.assertTrue(command.endswith(mode+')'))

    def test_release_checksums_include_zip(self):
        names=[]
        for line in (OUT/'SHA256SUMS').read_text().splitlines():
            digest,name=line.split('  ',1);names.append(name)
            self.assertEqual(hashlib.sha256((OUT/name).read_bytes()).hexdigest(),digest,name)
        self.assertIn('quick-v-0.6.5-dona-0.1.0-beta.2.zip',names)
        with zipfile.ZipFile(OUT/'quick-v-0.6.5-dona-0.1.0-beta.2.zip') as z:self.assertIsNone(z.testzip())

    def test_actual_helper_file_import_contract(self):
        d=json.loads((OUT/'dona-broadcast.tavern-helper.json').read_text(encoding='utf-8'))
        self.assertEqual(set(d),{'type','enabled','name','id','content','info','button','data','export_with'})
        self.assertEqual(d['type'],'script');self.assertFalse(d['enabled'])
        self.assertEqual(d['name'],'dona快V · 战术播报');self.assertEqual(d['data'],{})
        self.assertEqual(d['button'],{'enabled':False,'buttons':[]})
        self.assertTrue(d['content'].startswith("import 'https://cdn.jsdelivr.net/gh/"))
        self.assertNotIn('@main',d['content']);self.assertNotIn('@latest',d['content'])

    def test_cloud_source_hash_matches_git_blob(self):
        raw=subprocess.check_output(['git','show','HEAD:frontend/broadcast/dona-broadcast.js'],cwd=ROOT)
        self.assertEqual(raw,(OUT/'dona-broadcast.js').read_bytes())
        loader=(OUT/'dona-cloud-loader.js').read_text(encoding='utf-8')
        self.assertIn(hashlib.sha256(raw).hexdigest(),loader)
        self.assertNotIn('setInterval',loader);self.assertNotIn('localStorage',loader)
        self.assertIn("credentials: 'omit'",loader)

    def test_fresh_install_not_misrepresented(self):
        d=json.loads((ROOT/'docs/resource-status.json').read_text(encoding='utf-8'))
        required=[x for x in d['resources'] if x['kind'] in ['runtime-apk-part','code-bundle-part']]
        self.assertEqual(len(required),9)
        self.assertEqual(sum(x['size'] for x in required if x['kind']=='runtime-apk-part'),d['runtimeApk']['size'])
        self.assertEqual(sum(x['size'] for x in required if x['kind']=='code-bundle-part'),d['codeBundle']['size'])
        if not d['freshInstallReady']:
            self.assertIn('全新安装资源阻塞',(ROOT/'README.md').read_text(encoding='utf-8'))
            self.assertFalse(json.loads((OUT/'version.json').read_text(encoding='utf-8'))['freshInstall']['ready'])

if __name__=='__main__':unittest.main()
