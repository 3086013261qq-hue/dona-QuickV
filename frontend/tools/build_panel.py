#!/usr/bin/env python3
"""Generate panel-only replacement files from the exact authorized 0.6.5 installer. Never execute it."""
import argparse, base64, hashlib, json
from pathlib import Path

EXPECTED = "95f944ba5483e8953bab59a8962cc04d5517fddee6f5913a1054d16db6137db5"
def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("installer", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = args.installer.read_bytes()
    if digest(raw) != EXPECTED:
        raise SystemExit("Unrecognized installer; review before porting")
    release, _ = json.JSONDecoder().raw_decode(raw.decode("utf-8").split("const RELEASE = ",1)[1])
    if release["version"] != "0.6.5":
        raise SystemExit("Unexpected release")
    def read(name):
        item = release["files"]["plugin/public/" + name]
        content = base64.b64decode(item["base64"],validate=True)
        if len(content) != item["size"] or digest(content) != item["sha256"]:
            raise SystemExit("Invalid asset: " + name)
        return content.decode("utf-8")
    html = read("index.html")
    changes = [
        ("<title>快速 V · SillyDroid</title>","<title>快速 V 0.6.5 · dona美化</title>"),
        ('<span class="eyebrow">SillyDroid · 快速 V 0.6.5</span>','<span class="eyebrow">LOCAL GATEWAY / TACTICAL TERMINAL</span>'),
        ('<h1 id="page-title">快速 V<span class="title-mark" aria-hidden="true">↗</span></h1>','<h1 id="page-title">快速 V 0.6.5<span class="title-mark" aria-hidden="true">↗</span></h1><p class="dona-credit">DONA 美化 · UI REV. 01</p>'),
    ]
    for old,new in changes:
        if html.count(old)!=1: raise SystemExit("Panel contract changed")
        html=html.replace(old,new)
    css = read("style.css")+"\n"+(Path(__file__).resolve().parents[1]/"theme"/"panel.css").read_text(encoding="utf-8")
    css += "\n.intro .dona-credit{display:inline-block;background:#f5d449;color:#101216;font-weight:800;padding:3px 8px;letter-spacing:.08em}\\n".replace("\\n","\n")
    args.output.mkdir(parents=True,exist_ok=True)
    for name,data in [("index.html",html),("style.css",css)]:
        (args.output/name).write_text(data,encoding="utf-8")
    print("Panel files generated; app.js and installer unchanged.")
if __name__=="__main__": main()
