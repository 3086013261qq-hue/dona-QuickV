/* Synthetic local mocks only. Does not load, require or execute any installer. */
'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { secureRequest, createPlugin } = require('../.local/release/payload/plugin/index.js');
const { failureStatus } = require('../.local/release/payload/plugin/lib/failure-status.cjs');
const { fields } = require('../integration/status-fields.cjs');

function response() {
  return { statusCode: 200, headers: {}, value: null,
    setHeader(k,v){this.headers[k]=v;}, status(code){this.statusCode=code;return this;},
    json(v){this.value=v;return this;} };
}
function request(extra={}) {
  return {method:'GET',path:'/failure-status',headers:{host:'127.0.0.1:8000',origin:'http://127.0.0.1:8000','sec-fetch-site':'same-origin'},
    socket:{remoteAddress:'127.0.0.1'},query:{trace:'a'.repeat(32)},...extra};
}
test('unchanged same-origin/loopback protection blocks remote and hostile origins',()=>{
  for (const extra of [
    {socket:{remoteAddress:'192.0.2.1'}},
    {headers:{host:'example.com'}},
    {headers:{host:'127.0.0.1:8000',origin:'https://attacker.example'}},
  ]){
    const res=response();let next=false;
    secureRequest(request(extra),res,()=>next=true);
    assert.equal(next,false);assert.equal(res.statusCode,403);
  }
});
test('unchanged mutation CSRF protection and body validation',()=>{
  const token='synthetic-test-token-only';
  const req=request({method:'POST',path:'/start',body:{},session:{csrfToken:token}});
  let next=false;const denied=response();secureRequest(req,denied,()=>next=true);
  assert.equal(next,false);assert.equal(denied.statusCode,403);
  req.headers['x-csrf-token']=token;req.headers['content-type']='application/json';
  const allowed=response();secureRequest(req,allowed,()=>next=true);assert.equal(next,true);
  next=false;req.body={unexpected:true};const invalid=response();secureRequest(req,invalid,()=>next=true);
  assert.equal(next,false);assert.equal(invalid.statusCode,400);
});
test('existing status route requires same-origin source and valid trace',async()=>{
  const routes={};
  const router={use(){},get:(path,fn)=>routes['GET '+path]=fn,post:(path,fn)=>routes['POST '+path]=fn};
  const client={request:async()=>({status:200,body:{phase:'running',attempts:[],retry_remaining_ms:0}})};
  const supervisor={waitStatusPassword:()=> 'synthetic-in-memory-placeholder',installed:()=>false};
  const plugin=createPlugin({supervisor,channelClient:client,setup:{},cookieSetup:{}});
  await plugin.init(router);
  const route=routes['GET /failure-status'];assert.equal(typeof route,'function');
  const cross=response();await route(request({headers:{host:'127.0.0.1:8000','sec-fetch-site':'cross-site'}}),cross);
  assert.equal(cross.statusCode,403);
  const invalid=response();await route(request({query:{trace:'../secret'}}),invalid);assert.equal(invalid.statusCode,400);
  const allowed=response();await route(request(),allowed);assert.equal(allowed.statusCode,200);
  assert.deepEqual(allowed.value,{phase:'running',attempts:[],retry_remaining_ms:0});
});
test('status sanitization drops unknown fields and invalid numeric values',()=>{
  const value=fields({dona:{version:1,attempt:2,maxAttempts:4,inputTokens:0,thinkingTokens:-1,outputTokens:true,totalTokens:Infinity,transferSeconds:NaN,cookie:'NEVER EXPOSE',model:'projects/PRIVATE',streaming:true}});
  assert.deepEqual(value,{dona:{version:1,attempt:2,maxAttempts:4,inputTokens:0,streaming:true}});
});
test('existing backend authentication is required before status can be read',async()=>{
  let called=false;
  await assert.rejects(failureStatus({waitStatusPassword:()=>null},{request(){called=true;}},'a'.repeat(32),new AbortController().signal),{status:503});
  assert.equal(called,false);
});
test('validated existing status snapshot forwards only sanitized additions',async()=>{
  const signal=new AbortController().signal;
  const raw={phase:'finished',attempts:[{attempt:1,code:429,reason:'http',message:'PRIVATE'}],retry_remaining_ms:0,
    dona:{version:1,inputTokens:12,totalTokens:17,transferSeconds:1.25,url:'PRIVATE'},cookie:'PRIVATE'};
  const result=await failureStatus({waitStatusPassword:()=> 'synthetic-in-memory-placeholder'},
    {request:async()=>({status:200,body:raw})},'a'.repeat(32),signal);
  assert.equal(result.dona.inputTokens,12);assert.ok(!JSON.stringify(result).includes('PRIVATE'));
});
