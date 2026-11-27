/* dona快V · 战术播报 v0.1.0 | Quick V 0.6.5 | visual only */
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
  let key='', dismissed='', timeout=null, raf=null, activeRun=null, seq=-1, bridge=false, destroyed=false;
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
      else if(p==='running')show('running:'+attempt,'正在继续生成',elapsed?'本轮用时 '+elapsed:'正在处理请求');
      else if(p==='failed')show('failed:'+attempt,'请求未完成',code?'HTTP '+code+' · '+error:'请查看原版故障提示','error');
      else if(p==='finished')show('recovered:'+attempt,'通讯已恢复','原版报告重试恢复','ok',2500);
      return;
    }
    if(elapsed)show('wait','正在生成','本轮用时 '+elapsed);
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
  const modelName=s=>typeof s==='string'&&/^[a-zA-Z0-9._-]{1,80}$/.test(s)?s:'';
  // Optional sanitized local bridge. No network access, credentials, or generation actions.
  function event(e){
    const d=e.detail;
    if(!d||d.version!==1||typeof d.runId!=='string'||!/^[a-zA-Z0-9_-]{1,96}$/.test(d.runId)||!validNumber(d.seq))return;
    if(d.type==='start'){
      if(seenRuns.has(d.runId))return;
      seenRuns.add(d.runId);if(seenRuns.size>64)seenRuns.delete(seenRuns.values().next().value);
      activeRun=d.runId;seq=-1;bridge=true;
    }
    if(!bridge||d.runId!==activeRun||d.seq<=seq)return;
    seq=d.seq;
    const model=modelName(d.model), prefix=activeRun+':';
    if(d.type==='start')show(prefix+'start','等待模型响应',model);
    else if(d.type==='retry'){
      const code=Number.isInteger(d.http)&&d.http>=400&&d.http<=599?d.http:null;
      const count=validNumber(d.attempt)&&d.attempt>0?d.attempt:null;
      const max=validNumber(d.maxAttempts)&&d.maxAttempts>=count?d.maxAttempts:null;
      const ms=validNumber(d.retryRemainingMs)?d.retryRemainingMs:null;
      show(prefix+'retry:'+count,codes[code]||'通讯异常',[code?'HTTP '+code:'',count?'重试 '+count+(max?'/'+max:''):'',ms!==null?'约 '+Math.ceil(ms/1000)+' 秒后重试':'',model].filter(Boolean).join(' · '));
    }else if(d.type==='connecting')show(prefix+'connecting','正在重新连接',model);
    else if(d.type==='streaming')show(prefix+'streaming','通讯已建立','正在流式输出','ok',2500);
    else if(d.type==='complete'){
      const items=[];
      for(const [k,label] of [['inputTokens','提示词'],['thinkingAndOutputTokens','思考与生成'],['totalTokens','总 Token']])if(validNumber(d[k]))items.push(label+'  '+d[k].toLocaleString('zh-CN'));
      if(typeof d.transferSeconds==='number'&&Number.isFinite(d.transferSeconds)&&d.transferSeconds>=0)items.push('成功传输  '+d.transferSeconds.toFixed(1)+'s');
      show(prefix+'complete','生成完毕 / 作战结算',items.join('\n')||'本轮未提供用量统计','ok',8000);
      activeRun=null; // Once an event bridge is active, it owns status until the next start event.
    }else if(d.type==='failed'||d.type==='cancelled'){
      show(prefix+d.type,d.type==='failed'?'请求未完成':'已取消',model,d.type==='failed'?'error':'wait',d.type==='cancelled'?2500:0);
      activeRun=null;
    }
  }
  doc.addEventListener('dona-qv:status',event);
  function visibility(){if(!doc.hidden)schedule();}
  doc.addEventListener('visibilitychange',visibility);
  function destroy(){if(destroyed)return;destroyed=true;observer.disconnect();if(raf!==null)host.cancelAnimationFrame(raf);hide();doc.removeEventListener('dona-qv:status',event);doc.removeEventListener('visibilitychange',visibility);style.remove();panel.remove();window.removeEventListener('pagehide',destroy);if(host[KEY]===destroy)delete host[KEY];}
  host[KEY]=destroy;window.addEventListener('pagehide',destroy,{once:true});schedule();
})();
