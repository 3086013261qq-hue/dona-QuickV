/* dona快V · 战术播报 v0.1.0 | Quick V 0.6.5 | visual only; private */
(() => {
  'use strict';
  let host, doc;
  try { host = window.parent; doc = host.document; } catch { return; }
  if (!doc.body || !host.MutationObserver) return;
  const ID = 'dona-qv-broadcast', KEY = '__donaQvBroadcastV1';
  host[KEY]?.();
  const style = doc.createElement('style');
  style.textContent = `
#dona-qv-broadcast{--accent:#f5d449;position:fixed;z-index:1000;top:max(12px,env(safe-area-inset-top));right:12px;width:min(310px,calc(100% - 24px));box-sizing:border-box;background:#101216;color:#edf0f3;border:1px solid #46505c;border-left:3px solid var(--accent);padding:11px 12px;font:13px/1.45 system-ui,sans-serif;box-shadow:0 6px 18px #0005;pointer-events:none;text-align:left}
#dona-qv-broadcast[hidden]{display:none!important}
#dona-qv-broadcast[data-tone="ok"]{--accent:#a8e3ac}
#dona-qv-broadcast[data-tone="error"]{--accent:#ff9390}
#dona-qv-broadcast .dq-head{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #39414b;padding-bottom:5px;color:#a7b0ba;font:700 10px/1.4 ui-monospace,monospace;letter-spacing:.06em}
#dona-qv-broadcast .dq-head b{color:var(--accent)}
#dona-qv-broadcast button{pointer-events:auto;background:transparent;color:#edf0f3;border:0;padding:0;width:44px;height:44px;margin:-9px -8px -7px 0;font-size:20px;cursor:pointer}
#dona-qv-broadcast .dq-title{margin:9px 0 2px;font-size:16px;font-weight:800;color:var(--accent)}
#dona-qv-broadcast .dq-detail{white-space:pre-line;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}
#dona-qv-broadcast .dq-line{height:2px;margin-top:10px;background:var(--accent)}
`;
  const panel = doc.createElement('aside'); panel.id = ID; panel.hidden = true;
  panel.setAttribute('aria-label','dona快V 战术播报');
  const el = (tag, cls, text) => { const n=doc.createElement(tag); n.className=cls; if(text)n.textContent=text; return n; };
  const head=el('div','dq-head'), close=el('button','dq-close','×');
  close.type='button'; close.setAttribute('aria-label','关闭播报');
  head.append(el('b','','◆ DONA / 通讯终端'),close);
  const title=el('div','dq-title'), detail=el('div','dq-detail');
  title.setAttribute('role','status'); title.setAttribute('aria-live','polite');
  panel.append(head,title,detail,el('div','dq-line'));
  doc.head.append(style); doc.body.append(panel);
  let key='', dismissed='', timeout=null, raf=null, activeRun=null, seq=-1, bridge=false, destroyed=false, tick=null, deadline=0, lastEvent=null;
  const seenRuns=new Set();
  function hide(){clearTimeout(timeout);timeout=null;panel.hidden=true;}
  function show(next,label,body,tone='wait',duration=0){
    const changed=next!==key;
    if(changed){key=next;dismissed='';clearTimeout(timeout);timeout=null;}
    if(dismissed===next)return;
    if(title.textContent!==label)title.textContent=label;
    if(detail.textContent!==body)detail.textContent=body;
    panel.dataset.tone=tone;
    const wasHidden=panel.hidden;panel.hidden=false;
    if(duration && timeout===null && (wasHidden||changed))timeout=setTimeout(()=>{dismissed=next;hide();},duration);
  }
  close.addEventListener('click',()=>{dismissed=key;hide();});
  const codes={400:'请求无效',401:'身份验证失败',403:'访问被拒绝',404:'资源不存在',408:'请求超时',413:'请求过大',429:'上游请求受限',500:'服务内部错误',502:'网关连接异常',503:'服务暂不可用',504:'上游响应超时'};
  function visible(n){return Boolean(n?.isConnected&&!n.hidden&&host.getComputedStyle(n).display!=='none');}
  function readDom(){
    if(destroyed||bridge||doc.hidden)return;
    const f=doc.getElementById('quick-v-failure-notice'), w=doc.getElementById('quick-v-chat-wait');
    const p=visible(f)?f.dataset.phase:'';
    const elapsed=visible(w)?(w.textContent.match(/\d{2,}:\d{2}/)?.[0]||''):'';
    if(p==='retry_wait'||p==='running'||p==='failed'||p==='finished'){
      const rows=f.querySelectorAll('ol li'), latest=rows[rows.length-1];
      const attempt=Number(latest?.value)||0;
      const headline=f.querySelector('.qv-failure-title')?.textContent||'';
      const code=Number(headline.match(/[（(]([45]\d\d)[）)]/)?.[1])||0;
      const feedback=f.querySelector('.qv-failure-feedback');
      const seconds=visible(feedback)?feedback.textContent.match(/约\s*(\d+)\s*秒后重试/)?.[1]:null;
      const error=codes[code]||'通讯异常';
      if(p==='retry_wait')show('retry:'+attempt,error,[code?'HTTP '+code:'',attempt?'第 '+attempt+' 次失败':'',seconds?'约 '+seconds+' 秒后重试':''].filter(Boolean).join(' · '));
      else if(p==='running')show('running:'+attempt,'正在重新连接',elapsed?'本轮用时 '+elapsed:'原版报告请求处理中');
      else if(p==='failed')show('failed:'+attempt,'请求未完成',code?'HTTP '+code+' · '+error:'请查看原版故障提示','error');
      else if(p==='finished')show('recovered:'+attempt,'通讯已恢复','原版报告重试恢复','ok',2500);
      return;
    }
    if(elapsed)show('wait','正在处理请求','本轮用时 '+elapsed);
    else {hide();key='';dismissed='';}
  }
  const sourceSelector='#quick-v-chat-wait,#quick-v-failure-notice';
  function relevant(node){const n=node?.nodeType===1?node:node?.parentElement;return Boolean(n?.closest?.(sourceSelector)||n?.querySelector?.(sourceSelector));}
  function schedule(){if(raf===null)raf=host.requestAnimationFrame(()=>{raf=null;readDom();});}
  const observer=new host.MutationObserver(records=>{
    if(bridge||doc.hidden)return;
    if(records.some(r=>r.type==='childList'?(relevant(r.target)&&r.target!==doc.body&&r.target!==doc.documentElement||[...r.addedNodes,...r.removedNodes].some(relevant)):relevant(r.target)))schedule();
  });
  observer.observe(doc.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['hidden','data-phase','style','class']});
  const validNumber=n=>Number.isSafeInteger(n)&&n>=0&&n<=1000000000;
  const modelName=s=>typeof s==='string'&&/^gemini-(?:4-(?:argon|carbon|neon|hydrogen)|3(?:\.\d)?-(?:flash|pro)(?:-lite|-image|-preview)?|nano-banana-2\.1)$/.test(s)?s:'';
  const types=new Set(['start','waiting','retry','connecting','streaming','complete','failed','cancelled','reset']);
  const reasons={network:'连接中断',timeout:'响应超时',invalid_response:'上游响应异常',http:'上游异常',unknown:'通讯异常'};
  function stopTick(){if(tick!==null)host.clearInterval(tick);tick=null;}
  // Installed extension publishes its already-authorized snapshots; no extra polls.
  function event(e){
    const d=e.detail;
    if(!d||d.version!==1||!types.has(d.type)||typeof d.runId!=='string'||!/^[a-zA-Z0-9_-]{1,96}$/.test(d.runId)||!validNumber(d.seq))return;
    if(d.type==='reset'&&lastEvent?.runId===d.runId&&d.seq>seq){stopTick();hide();seq=d.seq;activeRun=null;lastEvent=null;return;}
    if(d.type==='start'||!bridge){
      if(seenRuns.has(d.runId))return;
      seenRuns.add(d.runId);if(seenRuns.size>64)seenRuns.delete(seenRuns.values().next().value);
      activeRun=d.runId;seq=-1;bridge=true;
    }
    if(!bridge||d.runId!==activeRun||d.seq<=seq)return;
    seq=d.seq;
    lastEvent={...d};stopTick();
    const model=modelName(d.model), prefix=activeRun+':';
    const retryInfo=validNumber(d.retryCount)&&validNumber(d.retryMax)&&d.retryCount<=d.retryMax?'已自动重试 '+d.retryCount+'/'+d.retryMax:'';
    if(d.type==='reset'){hide();activeRun=null;lastEvent=null;return;}
    if(d.type==='start'||d.type==='waiting')show(prefix+'start','正在等待模型响应',model);
    else if(d.type==='retry'){
      const code=Number.isInteger(d.http)&&d.http>=400&&d.http<=599?d.http:null;
      const count=validNumber(d.attempt)&&d.attempt>0?d.attempt:null;
      const max=validNumber(d.maxAttempts)&&d.maxAttempts>=count?d.maxAttempts:null;
      const ms=validNumber(d.retryRemainingMs)?d.retryRemainingMs:null;
      deadline=ms===null?0:host.performance.now()+ms;
      const draw=()=>show(prefix+'retry:'+count,codes[code]||reasons[d.reason]||'通讯异常',[code?'HTTP '+code:'',count?'尝试 '+count+(max?'/'+max:''):'',retryInfo,ms!==null?'剩余等待 '+Math.ceil(Math.max(0,deadline-host.performance.now())/1000)+' 秒':'',model].filter(Boolean).join(' · '));
      draw();
      if(ms>0&&!doc.hidden)tick=host.setInterval(()=>{draw();if(host.performance.now()>=deadline)stopTick();},1000);
    }else if(d.type==='connecting')show(prefix+'connecting','正在重新连接',[retryInfo,model].filter(Boolean).join(' · '));
    else if(d.type==='streaming')show(prefix+'streaming','通讯已建立 · 正在生成','正在流式输出','ok');
    else if(d.type==='complete'){
      const items=[];
      for(const [k,label] of [['inputTokens','提示词'],['thinkingAndOutputTokens','思考与生成'],['totalTokens','总 Token']])if(validNumber(d[k]))items.push(label+'  '+d[k].toLocaleString('zh-CN'));
      if(!validNumber(d.thinkingAndOutputTokens))for(const [k,label] of [['thinkingTokens','思考'],['outputTokens','生成']])if(validNumber(d[k]))items.push(label+'  '+d[k].toLocaleString('zh-CN'));
      if(typeof d.transferSeconds==='number'&&Number.isFinite(d.transferSeconds)&&d.transferSeconds>=0&&d.transferSeconds<=86400)items.push('成功传输  '+d.transferSeconds.toFixed(1)+'s');
      show(prefix+'complete','生成完毕 / 作战结算',items.join('\n')||'本轮未提供用量统计','ok',8000);
      activeRun=null; // Once an event bridge is active, it owns status until the next start event.
    }else if(d.type==='failed'||d.type==='cancelled'){
      const code=Number.isInteger(d.http)&&d.http>=400&&d.http<=599?d.http:null;
      show(prefix+d.type,d.type==='failed'?'请求失败':'已取消',[code?'HTTP '+code:'',d.type==='failed'?(codes[code]||reasons[d.reason]||'通讯异常'):'',model].filter(Boolean).join(' · '),d.type==='failed'?'error':'wait',d.type==='cancelled'?2500:0);
      activeRun=null;
    }
  }
  doc.addEventListener('dona-qv:status',event);
  function visibility(){if(doc.hidden)stopTick();else {schedule();if(lastEvent?.type==='retry'&&activeRun){const value={...lastEvent,retryRemainingMs:Math.max(0,Math.ceil(deadline-host.performance.now()))};seq--;event({detail:value});}}}
  doc.addEventListener('visibilitychange',visibility);
  function viewport(){const v=host.visualViewport;panel.style.top=`max(${12+(v?.offsetTop||0)}px,env(safe-area-inset-top))`;}
  host.visualViewport?.addEventListener('resize',viewport);host.visualViewport?.addEventListener('scroll',viewport);viewport();
  function pagehide(e){if(e.persisted){stopTick();observer.disconnect();}else destroy();}
  function pageshow(e){if(e.persisted&&!destroyed){observer.observe(doc.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['hidden','data-phase','style','class']});visibility();}}
  function destroy(){if(destroyed)return;destroyed=true;observer.disconnect();stopTick();if(raf!==null)host.cancelAnimationFrame(raf);hide();doc.removeEventListener('dona-qv:status',event);doc.removeEventListener('visibilitychange',visibility);host.visualViewport?.removeEventListener('resize',viewport);host.visualViewport?.removeEventListener('scroll',viewport);style.remove();panel.remove();window.removeEventListener('pagehide',pagehide);window.removeEventListener('pageshow',pageshow);host.removeEventListener('pagehide',pagehide);host.removeEventListener('pageshow',pageshow);if(host[KEY]===destroy)delete host[KEY];}
  host[KEY]=destroy;window.addEventListener('pagehide',pagehide);window.addEventListener('pageshow',pageshow);if(host!==window){host.addEventListener('pagehide',pagehide);host.addEventListener('pageshow',pageshow);}schedule();
  doc.dispatchEvent(new host.CustomEvent('dona-qv:subscribe'));
})();
