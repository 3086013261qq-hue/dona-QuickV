import ast
import base64
import copy
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_release as b


class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.items = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        # The only new element is the existing design's credit paragraph.
        if ('class', 'dona-credit') not in attrs:
            self.items.append((tag, attrs))


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.release = b.load_release(ROOT / 'install-0.6.5.cjs')
        cls.output = ROOT / '.local/release'
        cls.built_source = next(cls.output.glob('install-quick-v-*.cjs')).read_text(encoding='utf-8')
        cls.built, _ = json.JSONDecoder().raw_decode(cls.built_source.split('const RELEASE = ', 1)[1])

    def test_only_release_literal_changes_in_installer(self):
        def outside(s):
            start = s.index('const RELEASE = ') + len('const RELEASE = ')
            _, n = json.JSONDecoder().raw_decode(s[start:])
            return s[:start] + s[start+n:]
        self.assertEqual(outside(self.source), outside(self.built_source))

    def test_all_assets_and_overlay_checksums(self):
        for meta in self.built['files'].values():
            b.verified(meta)
        self.assertEqual(len(b.overlay_files(self.built)), 50)

    def test_unchanged_business_js_and_security(self):
        changed = {'plugin/public/index.html', 'plugin/public/style.css', 'plugin/lib/failure-status.cjs', 'extension/failure-client.js'}
        for name, meta in self.release['files'].items():
            if name not in changed:
                self.assertEqual(meta, self.built['files'][name], name)
        for key in ['apk', 'assets', 'reuseCoreFiles', 'reuseLinks', 'runtimeRevision', 'appRevision']:
            self.assertEqual(self.release[key], self.built[key], key)
        old = b.overlay_files(self.release)
        new = b.overlay_files(self.built)
        for name in old:
            if name not in {'app/failure_status.py', 'app/api_helpers.py', 'app/wait_policy.py', 'app/pvp.py', 'app/upstreams/cookie_proxy.py'}:
                self.assertEqual(old[name], new[name], name)

    def test_panel_element_and_accessibility_contract(self):
        old = b.verified(self.release['files']['plugin/public/index.html']).decode()
        new = b.verified(self.built['files']['plugin/public/index.html']).decode()
        self.assertEqual(Elements(old).items, Elements(new).items)
        self.assertIn('<title>快速 V 0.6.5 · dona美化</title>', new)
        self.assertIn('h1 id="page-title">快速 V 0.6.5 · dona美化', new)
        css = b.verified(self.built['files']['plugin/public/style.css'])
        self.assertTrue(css.startswith(b.verified(self.release['files']['plugin/public/style.css'])))
        self.assertIn((ROOT / 'frontend/theme/panel.css').read_text(encoding='utf-8').strip(), css.decode())

    def test_application_hooks_do_not_change_business_ast(self):
        class StripHooks(ast.NodeTransformer):
            def visit_Import(self, node):
                return None if any(n.name == 'dona_status' for n in node.names) else node
            def visit_Expr(self, node):
                call = node.value
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                    root = call.func.value
                    if isinstance(root, ast.Name) and root.id == 'dona_status':
                        return None
                    if isinstance(root, ast.Call) and isinstance(root.func, ast.Name) and root.func.id == '__import__' and root.args[0].value == 'dona_status':
                        return None
                return self.generic_visit(node)
            def visit_AnnAssign(self, node):
                return None if isinstance(node.target, ast.Name) and node.target.id == 'dona' else node
            def visit_Dict(self, node):
                kept = [(k,v) for k,v in zip(node.keys,node.values) if not(k is None and isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and isinstance(v.func.value, ast.Name) and v.func.value.id == 'dona_status')]
                node.keys, node.values = [k for k,v in kept], [v for k,v in kept]
                return self.generic_visit(node)
        old, new = b.overlay_files(self.release), b.overlay_files(self.built)
        for name in old:
            if old[name] != new[name] and name.endswith('.py'):
                cleaned = StripHooks().visit(ast.parse(new[name][0]))
                self.assertEqual(ast.dump(ast.parse(old[name][0])), ast.dump(cleaned), name)

    def test_bad_input_and_patch_contract_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as folder:
            file = Path(folder) / 'bad.cjs'
            file.write_text('throw new Error("must never execute");')
            with self.assertRaises(SystemExit): b.load_release(file)
        bad = copy.deepcopy(self.release['files']['plugin/public/app.js'])
        bad['sha256'] = '0'*64
        with self.assertRaises(ValueError): b.verified(bad)
        with self.assertRaises(ValueError): b.replace('missing', 'contract', 'x')

    def test_reproducible_overlay_and_syntax(self):
        files = b.overlay_files(self.release)
        b.patch_application(files)
        self.assertEqual(b.pack_overlay(files), base64.b64decode(self.built['appOverlayBase64']))
        for name, (data, _) in files.items():
            if name.endswith('.py'): compile(data, name, 'exec')
        subprocess.run(['node', '--check', str(next(self.output.glob('install-quick-v-*.cjs')))], check=True, capture_output=True)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class StatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = {name: sys.modules.get(name) for name in ['region_recent','dona_status','failure_status']}
        sys.modules['region_recent'] = types.SimpleNamespace(note_result=lambda *a:None, mark_incomplete=lambda:None)
        cls.status = load_module('dona_status', ROOT / 'integration/dona_status.py')
        cls.fail = load_module('failure_status', ROOT / '.local/release/overlay/app/failure_status.py')
    @classmethod
    def tearDownClass(cls):
        for name, mod in cls.previous.items():
            if mod is None: sys.modules.pop(name, None)
            else: sys.modules[name] = mod
    def setUp(self):
        self.fail.histories = self.fail.FailureHistories()
        self.trace = 'a'*32
        self.token = self.fail.bind_request(self.trace)
    def tearDown(self): self.fail.unbind_request(self.token)
    def snapshot(self): return self.fail.histories.snapshot(self.trace)

    def test_retry_success_real_usage(self):
        self.status.limit(3,attempt=0)
        self.fail.note_running()
        self.fail.note_failure(429,'http')
        self.fail.note_retry_wait(5)
        snap = self.snapshot()
        self.assertEqual(snap['phase'],'retry_wait')
        self.assertTrue(0 < snap['retry_remaining_ms'] <= 5000)
        self.assertEqual(snap['dona']['maxAttempts'],4)
        self.assertEqual(snap['dona']['retryCount'],0)
        self.assertEqual(snap['dona']['retryMax'],3)
        self.fail.note_running()
        self.fail.note_failure(502,'network')
        self.fail.note_running()
        self.status.progress()
        self.status.usage(dict(promptTokenCount=72019,thoughtsTokenCount=4000,candidatesTokenCount=6936,totalTokenCount=82955),studio=True)
        self.assertNotIn('inputTokens',self.snapshot()['dona'])
        self.status.success(None,143.1)
        self.fail.note_terminal('finished')
        snap = self.snapshot()['dona']
        self.assertEqual(snap['thinkingAndOutputTokens'],10936)
        self.assertEqual(snap['transferSeconds'],143.1)
        self.assertEqual(snap['totalTokens'],82955)

    def test_absent_partial_and_zero_usage_are_distinct(self):
        self.fail.note_running()
        self.status.usage(dict(prompt_token_count=0,total_token_count=0))
        self.fail.note_terminal('finished')
        d=self.snapshot()['dona']
        self.assertEqual(d['inputTokens'],0)
        self.assertNotIn('thinkingAndOutputTokens',d)
        self.assertNotIn('transferSeconds',d)

    def test_failure_cancel_and_duplicate_terminal(self):
        self.fail.note_running()
        self.status.usage(dict(prompt_token_count=50))
        self.fail.note_terminal('cancelled')
        self.fail.note_terminal('finished')
        self.assertEqual(self.snapshot()['phase'],'cancelled')
        self.assertNotIn('inputTokens',self.snapshot()['dona'])

    def test_retry_discards_failed_attempt_usage(self):
        self.fail.note_running()
        self.status.usage(dict(prompt_token_count=500))
        self.status.progress()
        self.fail.note_running()
        self.fail.note_terminal('finished')
        self.assertNotIn('inputTokens',self.snapshot()['dona'])
        self.assertFalse(self.snapshot()['dona']['streaming'])

    def test_allowlist_and_isolation(self):
        self.status.usage({'prompt_token_count': True,'total_token_count': float('nan'),'api_key':'SENSITIVE','cookie':'SENSITIVE'})
        other = self.fail.bind_request('b'*32)
        self.status.usage(dict(prompt_token_count=123))
        self.fail.note_terminal('finished')
        self.fail.unbind_request(other)
        self.fail.note_terminal('finished')
        self.assertNotIn('inputTokens',self.snapshot()['dona'])
        self.assertNotIn('SENSITIVE',json.dumps(self.snapshot()))
        self.assertEqual(self.fail.histories.snapshot('b'*32)['dona']['inputTokens'],123)

    def test_resume_binding_follows_original_producer(self):
        buf=types.SimpleNamespace(done=False)
        self.fail.bind_buffer(buf,True)
        other=self.fail.bind_request('b'*32)
        self.fail.bind_buffer(buf,False)
        self.status.usage(dict(prompt_token_count=12))
        self.fail.note_terminal('finished')
        self.assertEqual(self.fail.histories.snapshot('b'*32)['dona']['inputTokens'],12)
        self.fail.unbind_request(other)
        self.assertEqual(self.snapshot()['dona']['inputTokens'],12)

    def test_memory_ttl_and_duplicate_trace(self):
        self.assertIsNone(self.fail.histories.begin(self.trace))
        for n in range(300): self.fail.histories.begin(f'{n:032x}')
        self.assertLessEqual(len(self.fail.histories.entries),256)
        self.fail.histories._prune(float('inf'))
        self.assertEqual(self.fail.histories.entries,{})


if __name__ == '__main__': unittest.main()
