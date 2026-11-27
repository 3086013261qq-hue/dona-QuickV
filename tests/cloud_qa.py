"""Real Chromium, mock CDN. Core integrity, imported JSON and helper iframe cleanup."""
import functools
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/beta'
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            context=browser.new_context(viewport={'width':390,'height':844})
            page=context.new_page();page.set_default_timeout(5000)
            page.goto(f'http://127.0.0.1:{server.server_port}/README.md')
            page.set_content('<div id="chat"></div>')
            calls=[];mode={'corrupt':False};core=(OUT/'dona-broadcast.js').read_bytes();loader=(OUT/'dona-cloud-loader.js').read_bytes()
            def route(r):
                calls.append(r.request.url)
                if r.request.url.endswith('/dona-broadcast.js'):
                    r.fulfill(body=(bytes([core[0]^1])+core[1:] if mode['corrupt'] else core),content_type='text/javascript',headers={'Access-Control-Allow-Origin':'*'})
                else:r.fulfill(body=loader,content_type='text/javascript',headers={'Access-Control-Allow-Origin':'*'})
            page.route('https://cdn.jsdelivr.net/**',route)
            item=json.loads((OUT/'dona-broadcast.tavern-helper.json').read_text(encoding='utf-8'))
            def enable():
                page.evaluate("const old=document.querySelector('iframe');if(old)old.remove();document.body.appendChild(document.createElement('iframe'))")
                frame=page.frames[-1]
                frame.evaluate("s=>{const n=document.createElement('script');n.type='module';n.textContent=s;document.head.append(n)}",item['content'])
                return frame
            frame=enable();panel=page.locator('#dona-qv-broadcast');expect(panel).to_have_count(1)
            assert len(calls)==2,calls
            page.evaluate("document.dispatchEvent(new CustomEvent('dona-qv:status',{detail:{version:1,runId:'cloud',seq:0,type:'start'}}))")
            expect(panel).to_be_visible();checks.append('Actual JSON content imports fixed CDN module; core checksum passes; single initial fetch')
            frame.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide'))")
            expect(panel).to_have_count(0);checks.append('Helper pagehide unload restores original document without a panel')
            frame=enable();expect(panel).to_have_count(1);checks.append('Re-enable in a new helper iframe loads again cleanly')
            frame.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide'))")
            mode['corrupt']=True;frame=enable()
            page.wait_for_timeout(300);expect(panel).to_have_count(0);checks.append('Corrupt CDN body never executes')
            assert page.evaluate('localStorage.length')==0
            assert not page.locator('#quick-v-chat-wait[hidden],#quick-v-failure-notice[hidden]').count()
            checks.append('No persistent state or original status mutations')
            browser.close()
    finally:server.shutdown();server.server_close()
    result={'environment':'Desktop Chromium mock CDN and same-origin helper iframe; Android pending','passed':checks}
    (ROOT/'.local/qa/cloud-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
