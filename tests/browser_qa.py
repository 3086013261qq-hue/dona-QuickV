"""Desktop Chromium emulation and synthetic events only; never calls a model."""
import functools
import http.server
import json
from pathlib import Path
import threading
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.local/qa'
SCRIPT = (ROOT / 'frontend/broadcast/dona-broadcast.js').read_text(encoding='utf-8')


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    handler=functools.partial(QuietHandler,directory=str(ROOT))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{server.server_port}'
    results=[]
    print('Starting local Chromium QA',flush=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            page=context.new_page()
            page.set_default_timeout(6000)
            errors=[]
            page.on('pageerror',lambda e: errors.append(str(e)))
            # Serve only generated static assets. All panel APIs are local test doubles.
            requests=[]
            state={'phase':'stopped','installed':True,'running':False,'busy':False,'message':'测试状态',
                'apiBase':'http://127.0.0.1:8051/v1','consoleUrl':'http://127.0.0.1:8051'}
            def route(r):
                url=urlparse(r.request.url)
                path=url.path
                if path.startswith('/api/plugins/quick-v/'):
                    name=path.removeprefix('/api/plugins/quick-v/') or 'index.html'
                    file=ROOT / '.local/release/payload/plugin/public' / name
                    if file.is_file() and file.resolve().is_relative_to((ROOT / '.local/release/payload/plugin/public').resolve()):
                        r.fulfill(path=str(file));return
                    requests.append((path,r.request.method))
                    if name=='status': r.fulfill(json=state);return
                    if name in ('start','stop'):
                        state.update(phase='running' if name=='start' else 'stopped',running=name=='start')
                        assert r.request.headers.get('x-csrf-token')=='qa-only-csrf-token'
                        r.fulfill(json=state);return
                    r.fulfill(status=503,json={'error':{'message':'测试端点暂不可用'}});return
                if path=='/csrf-token': r.fulfill(json={'token':'qa-only-csrf-token'});return
                if not r.request.url.startswith(origin): r.abort();return
                r.continue_()
            page.route('**/*',route)
            page.goto(origin+'/api/plugins/quick-v/')
            expect(page.locator('#phase-label')).to_have_text('已停止')
            page.locator('#advanced-settings > summary').click()
            page.locator('#start-button').click()
            expect(page.locator('#phase-label')).to_have_text('已启动')
            page.locator('#stop-button').click()
            expect(page.locator('#phase-label')).to_have_text('已停止')
            results.append('Original app.js start/stop + CSRF request flow (mock service)')
            print('Panel start/stop passed',flush=True)
            for width,height in [(320,740),(390,844),(430,932),(844,390),(390,320)]:
                page.set_viewport_size({'width':width,'height':height})
                # Expand all original sections to expose layout, fields and dialogs.
                page.evaluate("document.querySelectorAll('details').forEach(n=>n.open=true)")
                for theme in ['light','dark']:
                    page.emulate_media(color_scheme=theme,reduced_motion='reduce')
                    page.screenshot(path=str(OUT / f'panel-{width}x{height}-{theme}.png'),full_page=True)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), f'Panel overflow {width}x{height}'
                results.append(f'Panel {width}x{height} light/dark + reduced motion')
            # All original input/ID attributes are separately checked by unittest.
            assert not errors,errors
            page.goto(origin+'/README.md')
            page.set_content('''<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0}#form_sheld{position:fixed;bottom:0;left:0;width:100%;height:64px}</style><div id="chat"></div><div id="form_sheld"><textarea id="send_textarea"></textarea><button id="mes_stop">停止</button></div>''')
            page.set_viewport_size({'width':390,'height':844})
            network_before=len(requests)
            page.add_script_tag(content=SCRIPT)
            panel=page.locator('#dona-qv-broadcast')
            expect(panel).to_be_hidden()
            def event(run,seq,kind,**fields):
                page.evaluate("d=>document.dispatchEvent(new CustomEvent('dona-qv:status',{detail:d}))",dict(version=1,runId=run,seq=seq,type=kind,**fields))
            event('one',0,'start')
            expect(panel).to_contain_text('正在等待模型响应')
            event('one',1,'retry',http=429,attempt=2,maxAttempts=4,retryRemainingMs=5000,retryCount=1,retryMax=3)
            expect(panel).to_contain_text('HTTP 429')
            expect(panel).to_contain_text('尝试 2/4')
            expect(panel).to_contain_text('已自动重试 1/3')
            page.screenshot(path=str(OUT/'broadcast-retry-429.png'))
            event('one',2,'retry',http=502,attempt=3,maxAttempts=4,retryRemainingMs=5000)
            expect(panel).to_contain_text('HTTP 502')
            page.clock.install()
            page.clock.fast_forward(2100)
            expect(panel).to_contain_text('剩余等待 3 秒')
            event('one',3,'connecting')
            expect(panel).to_contain_text('正在重新连接')
            event('one',4,'streaming')
            expect(panel).to_contain_text('通讯已建立 · 正在生成')
            event('one',5,'complete',inputTokens=72019,thinkingAndOutputTokens=10936,totalTokens=82955,transferSeconds=143.1)
            expect(panel).to_contain_text('72,019')
            expect(panel).to_contain_text('10,936')
            expect(panel).to_contain_text('82,955')
            expect(panel).to_contain_text('143.1s')
            page.screenshot(path=str(OUT/'broadcast-complete.png'))
            page.clock.fast_forward(8100)
            expect(panel).to_be_hidden()
            event('two',0,'start')
            event('one',100,'failed',http=500)
            expect(panel).to_contain_text('等待模型响应')
            event('two',1,'complete')
            expect(panel).to_contain_text('本轮未提供用量统计')
            event('two',1,'complete',inputTokens=999)
            expect(panel).not_to_contain_text('999')
            event('three',0,'start')
            event('three',1,'cancelled')
            expect(panel).to_contain_text('已取消')
            event('four',0,'start')
            event('four',1,'failed',http=403,reason='http',model='projects/SECRET/models/x',cookie='SECRET',inputTokens='SECRET')
            expect(panel).to_contain_text('访问被拒绝')
            expect(panel).not_to_contain_text('SECRET')
            event('four',2,'reset')
            expect(panel).to_be_hidden()
            event('five',0,'start')
            event('five',1,'retry',http=429,retryRemainingMs=5000)
            panel.locator('button').click()
            event('five',2,'retry',http=429,retryRemainingMs=4000)
            expect(panel).to_be_hidden()
            event('five',3,'streaming')
            expect(panel).to_be_visible()
            # A changed run owns the single panel. Invalid events cannot seize it.
            event('hostile',0,'unrecognized')
            event('five',4,'complete',inputTokens=-1,totalTokens=float('inf'),transferSeconds=-1)
            expect(panel).to_contain_text('本轮未提供用量统计')
            assert len(requests)==network_before
            results.append('Broadcast replay: retry countdown, reconnect, stream, raw totals, no usage, cancel, failure, reset, stale/duplicate/invalid events, close')
            for width,height in [(320,740),(390,844),(430,932),(844,390),(390,320)]:
                page.set_viewport_size({'width':width,'height':height})
                event('layout'+str(width)+str(height),0,'start')
                box=panel.bounding_box()
                stop=page.locator('#mes_stop').bounding_box()
                assert box['x']>=0 and box['x']+box['width']<=width
                assert box['y']+box['height']<stop['y'],(box,stop)
                page.locator('#send_textarea').focus()
                page.screenshot(path=str(OUT/f'broadcast-{width}x{height}.png'))
            results.append('Broadcast mobile widths, landscape, keyboard-height simulation, input/stop separation')
            page.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}));window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
            event('bfcache',0,'start')
            expect(panel).to_be_visible()
            page.add_script_tag(content=SCRIPT)
            assert panel.count()==1
            page.evaluate('window.__donaQvBroadcastV1()')
            expect(panel).to_have_count(0)
            event('afterdestroy',0,'start')
            expect(panel).to_have_count(0)
            # Same-origin helper iframe, independent script pagehide, and reinjection.
            page.evaluate("const f=document.createElement('iframe');f.id='helper';document.body.append(f)")
            frame=page.frame_locator('#helper')
            page.frames[-1].evaluate(SCRIPT)
            assert panel.count()==1
            page.frames[-1].evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide'))")
            assert panel.count()==0
            results.append('Lifecycle: BFCache simulation, reinjection singleton, unload cleanup, same-origin helper iframe')
            # Exercise actual patched failure-client.js with the host bus and original polls.
            page.clock.resume()
            page.add_script_tag(content=SCRIPT)
            integration=page.evaluate("""async()=>{
              const {installChatFailures}=await import('/.local/release/payload/extension/failure-client.js');
              const events={};const listeners={};
              for(const n of ['GENERATION_AFTER_COMMANDS','GENERATE_AFTER_DATA','CHAT_COMPLETION_SETTINGS_READY','GENERATION_ENDED','GENERATION_STOPPED','CHAT_CHANGED'])events[n]=n;
              const bus={on:(n,h)=>(listeners[n]??=[]).push(h)};
              const fire=async(n,...args)=>{for(const h of listeners[n]||[])await h(...args)};
              const settings={chat_completion_source:'custom',custom_url:'http://127.0.0.1:8051/v1',custom_model:'gemini-4-argon'};
              const ctx={eventSource:bus,eventTypes:events,mainApi:'openai',chatCompletionSettings:settings,chat:[],chatId:1,characterId:1};
              const snapshots=[{phase:'running',attempts:[],retry_remaining_ms:0,dona:{version:1,attempt:1,maxAttempts:2}},
                {phase:'retry_wait',attempts:[{attempt:1,code:429,reason:'http'}],retry_remaining_ms:5000,dona:{version:1,attempt:1,maxAttempts:2}},
                {phase:'running',attempts:[{attempt:1,code:429,reason:'http'}],retry_remaining_ms:0,dona:{version:1,attempt:2,maxAttempts:2,streaming:true}},
                {phase:'finished',attempts:[{attempt:1,code:429,reason:'http'}],retry_remaining_ms:0,dona:{version:1,inputTokens:12,thinkingAndOutputTokens:5,totalTokens:17,transferSeconds:1.25}}];
              const calls=[];const received=[];
              const fake={fetch:(url,init)=>{calls.push(url);return Promise.resolve(new Response(JSON.stringify(url.startsWith('/api/plugins/')?(snapshots.shift()||{phase:'unknown',attempts:[],retry_remaining_ms:0}):{}),{status:200}))},addEventListener(){}};
              document.addEventListener('dona-qv:status',e=>received.push(e.detail.type));
              installChatFailures(()=>ctx,{clear(){},update(){}},{yaml:{parse:JSON.parse},isGenerating:()=>true,browser:fake,doc:document});
              await fire('GENERATION_AFTER_COMMANDS','normal',{},false);
              const message={role:'user',content:'SYNTHETIC'};
              await fire('GENERATE_AFTER_DATA',{prompt:[message]},false);
              const data={...settings,type:'normal',messages:[message],stream:true};
              await fire('CHAT_COMPLETION_SETTINGS_READY',data);
              await fake.fetch('/api/backends/chat-completions/generate',{method:'POST',body:JSON.stringify(data)});
              await new Promise(r=>setTimeout(r,2600));
              const completedText=document.querySelector('#dona-qv-broadcast').textContent;
              // A second real host lifecycle must preserve the cancellation notice.
              await fire('GENERATION_AFTER_COMMANDS','normal',{},false);
              const message2={role:'user',content:'SYNTHETIC CANCEL'};
              await fire('GENERATE_AFTER_DATA',{prompt:[message2]},false);
              const data2={...settings,type:'normal',messages:[message2],stream:true};
              await fire('CHAT_COMPLETION_SETTINGS_READY',data2);
              await fake.fetch('/api/backends/chat-completions/generate',{method:'POST',body:JSON.stringify(data2)});
              await fire('GENERATION_STOPPED');
              const cancelledText=document.querySelector('#dona-qv-broadcast').textContent;
              // If status is unavailable after the host ends, hide uncertain state.
              await fire('GENERATION_AFTER_COMMANDS','normal',{},false);
              const message3={role:'user',content:'SYNTHETIC UNKNOWN'};
              await fire('GENERATE_AFTER_DATA',{prompt:[message3]},false);
              const data3={...settings,type:'normal',messages:[message3],stream:true};
              await fire('CHAT_COMPLETION_SETTINGS_READY',data3);
              await fake.fetch('/api/backends/chat-completions/generate',{method:'POST',body:JSON.stringify(data3)});
              const realNow=Date.now;
              const ending=fire('GENERATION_ENDED');
              Date.now=()=>realNow()+5000;
              await ending;
              await new Promise(r=>setTimeout(r,50));
              Date.now=realNow;
              return {calls,received,completedText,cancelledText};
            }""")
            assert integration['received']==['start','waiting','retry','streaming','complete','reset','start','cancelled','start','reset'],integration
            assert len(integration['calls'])==8,integration
            assert '总 Token  17' in integration['completedText']
            assert '已取消' in integration['cancelledText']
            expect(panel).to_be_hidden()
            page.evaluate("document.dispatchEvent(new CustomEvent('dona-qv:subscribe'))")
            expect(panel).to_be_hidden()
            results.append('Actual patched extension: original request tracing + four existing status polls → bridge → broadcast; no extra generation or polling')
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close()
        (OUT/'browser-results.json').write_text(json.dumps({'environment':'Desktop Chromium emulation, synthetic local mocks; no Android device or provider calls','passed':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':len(results),'checks':results},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
