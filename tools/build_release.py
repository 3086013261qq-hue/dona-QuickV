#!/usr/bin/env python3
"""Static, pinned private rebuild. Never import or execute either installer."""
import argparse
import base64
import copy
import gzip
import io
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend/tools"))
from build_panel import build_panel, load_release, digest

REVISION = "0.1.0"


def replace(source, old, new, count=1):
    if source.count(old) != count:
        raise ValueError("Upstream patch contract changed: " + old[:75])
    return source.replace(old, new)


def verified(meta, encoded=None):
    data = base64.b64decode(meta["base64"] if encoded is None else encoded, validate=True)
    if len(data) != meta["size"] or digest(data) != meta["sha256"]:
        raise ValueError("Embedded asset integrity failure")
    return data


def overlay_files(release):
    data = verified(release["codeBundle"]["appOverlay"], release["appOverlayBase64"])
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for item in archive:
            name = item.name
            if item.isdir():
                continue
            if not item.isfile() or name.startswith('/') or '\\' in name or '..' in PurePosixPath(name).parts or name in files:
                raise ValueError("Unsafe upstream archive")
            files[name] = (archive.extractfile(item).read(), item.mode)
    if sum(len(data) for data, _ in files.values()) != release["codeBundle"]["appOverlay"]["unpackedSize"]:
        raise ValueError("Overlay expanded size mismatch")
    return files


def pack_overlay(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, (data, mode) in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size, item.mode, item.mtime = len(data), mode, 0
            archive.addfile(item, io.BytesIO(data))
    return gzip.compress(buf.getvalue(), mtime=0)


def patch_application(files):
    def patch(name, callback):
        data, mode = files["app/" + name]
        files["app/" + name] = (callback(data.decode("utf-8")).encode("utf-8"), mode)
    def failure(s):
        s = replace(s, 'import region_recent\n', 'import region_recent\nimport dona_status\n')
        s = replace(s, '    started: float\n', '    started: float\n    dona: dict = field(default_factory=dict)\n')
        s = replace(s, '            "retry_remaining_ms": remaining,', '            "retry_remaining_ms": remaining,\n            **dona_status.snapshot(self),')
        s = replace(s, '        binding.entry.attempt += 1', '        dona_status.reset()\n        binding.entry.attempt += 1')
        return s
    patch("failure_status.py", failure)
    def helpers(s):
        s = replace(s, 'from failure_status import failure_details, note_failure, note_terminal', 'import dona_status\nfrom failure_status import failure_details, note_failure, note_terminal')
        s = replace(s, '    usage_metadata = getattr(resp, "usage_metadata", None)', '    usage_metadata = getattr(resp, "usage_metadata", None)\n    dona_status.usage(usage_metadata)')
        s = replace(s, '                                                first_tok_mono = time.monotonic()', '                                                first_tok_mono = time.monotonic()\n                                                dona_status.progress()')
        s = replace(s, '                                                _up, _uth, _uout, _utp, _utot = _extract_raw_usage_fields(chunk_item_call)', '                                                dona_status.usage(chunk_item_call.usage_metadata)\n                                                _up, _uth, _uout, _utp, _utot = _extract_raw_usage_fields(chunk_item_call)')
        s = replace(s, '        region_recent.settle(True, 200)', '        dona_status.success(ttft, gen_time)\n        region_recent.settle(True, 200)')
        return s
    patch("api_helpers.py", helpers)
    def cookie(s):
        s = replace(s, 'from failure_status import failure_details, note_failure, note_running, note_terminal', 'import dona_status\nfrom failure_status import failure_details, note_failure, note_running, note_terminal')
        anchor = '    p_tk, th_tk, out_tk, t_tk = _extract_studio_usage_detail(usage_meta)'
        s = replace(s, anchor, '    dona_status.usage(usage_meta, studio=True)\n' + anchor)
        # Every first actual Cookie content/thought/tool/image timestamp, never heartbeat.
        lines = s.splitlines(keepends=True)
        hits = 0
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == 'first_tok_t0 = time.monotonic()':
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                lines.insert(i + 1, indent + 'dona_status.progress()\n')
                hits += 1
        if hits != 4:
            raise ValueError("Cookie progress contract changed")
        return ''.join(lines)
    patch("upstreams/cookie_proxy.py", cookie)
    patch("wait_policy.py", lambda s: replace(replace(s, 'import region_recent\n', 'import region_recent\nimport dona_status\n'), '        note_running()', '        dona_status.limit(self.policy["retry_max"], attempt=self.attempt)\n        note_running()'))
    patch("pvp.py", lambda s: replace(s, '                        note_running()', '                        __import__("dona_status").limit(job.settings["max_attempts"], retries=False)\n                        note_running()'))
    files["app/dona_status.py"] = ((ROOT / "integration/dona_status.py").read_bytes(), 0o644)


def patch_extension(data):
    s = data.decode("utf-8")
    s = "import { createDonaBridge } from './dona-bridge.js';\n" + s
    s = replace(s, '  let current = null;', '  let current = null;\n  const dona = createDonaBridge(doc);')
    s = replace(s, '    if (current) {\n      detach(current);', "    if (current) {\n      if (!current.donaKeep) dona.emit(current, 'reset');\n      detach(current);")
    s = replace(s, "    if (!snapshot || snapshot.phase === 'unknown'", "    if (run.done && !snapshot) dona.emit(run, 'reset');\n    dona.update(run, snapshot);\n    if (!snapshot || snapshot.phase === 'unknown'")
    s = replace(s, '      run.dispatched = true;', "      run.dispatched = true;\n      dona.emit(run, 'start');")
    s = replace(s, "  on('GENERATION_STOPPED', clear);", "  on('GENERATION_STOPPED', () => { if (current) { dona.emit(current, 'cancelled'); current.donaKeep = true; } clear(); });")
    return s.encode("utf-8")


def build(installer, output):
    source, original = load_release(installer)
    release = copy.deepcopy(original)
    assets = {name: verified(meta) for name, meta in release["files"].items()}
    panel = build_panel(release, output / "panel")
    assets.update({'plugin/public/' + name: data for name, data in panel.items()})
    assets['extension/failure-client.js'] = patch_extension(assets['extension/failure-client.js'])
    assets['extension/dona-bridge.js'] = (ROOT / 'integration/broadcast-bridge.js').read_bytes()
    key = 'plugin/lib/failure-status.cjs'
    assets[key] = replace(assets[key].decode('utf-8'), 'return { phase: raw.phase, attempts, retry_remaining_ms: raw.retry_remaining_ms };', "return { phase: raw.phase, attempts, retry_remaining_ms: raw.retry_remaining_ms, ...require('./dona-status.cjs').fields(raw) };").encode('utf-8')
    assets['plugin/lib/dona-status.cjs'] = (ROOT / 'integration/status-fields.cjs').read_bytes()
    overlay = overlay_files(release)
    before = copy.deepcopy(overlay)
    patch_application(overlay)
    # Keep upstream version/revision markers for its existing compatibility checks.
    packed = pack_overlay(overlay)
    release['appOverlayBase64'] = base64.b64encode(packed).decode('ascii')
    release['codeBundle']['appOverlay'].update(size=len(packed), sha256=digest(packed), unpackedSize=sum(len(d) for d, _ in overlay.values()))
    for name, data in assets.items():
        release['files'][name] = dict(size=len(data), sha256=digest(data), base64=base64.b64encode(data).decode('ascii'), mode=original['files'].get(name, {}).get('mode', 0o644))
    release['donaRevision'] = REVISION
    start = source.index('const RELEASE = ') + len('const RELEASE = ')
    _, length = json.JSONDecoder().raw_decode(source[start:])
    literal = json.dumps(release, ensure_ascii=False, separators=(',', ':'))
    built = source[:start] + literal + source[start + length:]
    # Only RELEASE differs: no installer code, authentication or retry rewrites.
    assert built[:start] == source[:start] and built[start + len(literal):] == source[start + length:]
    output.mkdir(parents=True, exist_ok=True)
    filename = 'install-quick-v-0.6.5-dona-' + REVISION + '.cjs'
    (output / filename).write_bytes(built.encode('utf-8'))
    # Inspection tree is private. Never commit any extracted upstream source.
    for name, data in assets.items():
        path = output / 'payload' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for name, (data, _) in overlay.items():
        path = output / 'overlay' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    broadcast = (ROOT / 'frontend/broadcast/dona-broadcast.js').read_bytes()
    (output / 'dona-broadcast.js').write_bytes(broadcast)
    (output / 'UPSTREAM-LICENSE').write_bytes(overlay['app/UPSTREAM-LICENSE'][0])
    for doc in ['installation.md', 'third-party-notices.md', 'testing.md']:
        if (ROOT / 'docs' / doc).exists():
            (output / doc).write_bytes((ROOT / 'docs' / doc).read_bytes())
    report = dict(upstreamVersion='0.6.5', donaRevision=REVISION,
        upstreamInstallerSha256=digest(Path(installer).read_bytes()), installerSha256=digest((output / filename).read_bytes()),
        changedEmbedded=[n for n, d in assets.items() if n not in original['files'] or digest(d) != original['files'][n]['sha256']],
        changedApplication=[n for n, d in overlay.items() if n not in before or d != before[n]],
        preservedEmbedded=[n for n, d in assets.items() if n in original['files'] and digest(d) == original['files'][n]['sha256']],
        overlay=release['codeBundle']['appOverlay'], externalResources='Original pinned HTTPS resources; downloaded only on explicit install',
        tests='See docs/testing.md; Android device verification pending')
    (output / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    deliverables = [filename, 'dona-broadcast.js', 'UPSTREAM-LICENSE', 'build-report.json', 'installation.md', 'third-party-notices.md', 'testing.md']
    sums = {name: digest((output / name).read_bytes()) for name in deliverables if (output / name).exists()}
    (output / 'SHA256SUMS').write_text(''.join(f'{sha}  {name}\n' for name, sha in sums.items()), encoding='utf-8')
    with zipfile.ZipFile(output / 'quick-v-0.6.5-dona-0.1.0-private.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in [*sums, 'SHA256SUMS']:
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, (output / name).read_bytes())
    print(json.dumps({k: v for k, v in report.items() if k not in ['preservedEmbedded', 'overlay']}, ensure_ascii=False, indent=2))
    return release, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('installer', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / '.local/release')
    args = parser.parse_args()
    build(args.installer, args.output)
