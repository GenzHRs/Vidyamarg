const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
function loadApi(fetch, env={}) {
  let token='first-user';
  const exports={};
  const source=fs.readFileSync(path.join(__dirname,'../services/api.ts'),'utf8');
  const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  const context={exports,require:()=>({useAuthStore:{getState:()=>({logout:()=>{}})}}),process:{env}, fetch,
    window:{location:{hostname:'staging.example.com',pathname:'/candidate'}},localStorage:{getItem:()=>token},
    Response, URL, URLSearchParams, Headers, FormData, setTimeout};
  vm.runInNewContext(js,context);
  return {api:exports, setToken:value=>{token=value;}};
}
test('deployment-specific HTTP and WebSocket URLs are respected on remote hosts',()=>{
  const {api}=loadApi(null,{NEXT_PUBLIC_API_URL:'https://api.example.com/api/v1',NEXT_PUBLIC_WS_URL:'wss://api.example.com/ws'});
  assert.equal(api.getBaseUrl(),'https://api.example.com/api/v1');
  assert.equal(api.getWsUrl(),'wss://api.example.com/ws');
});
test('GET responses cannot cross authentication boundaries through URL cache',async()=>{
  const calls=[];
  const {api,setToken}=loadApi(async(url,init)=>{calls.push(init);return Response.json({owner:init.headers.Authorization});});
  assert.equal((await api.apiService.getProfile()).owner,'Bearer first-user');
  setToken('second-user');
  assert.equal((await api.apiService.getProfile()).owner,'Bearer second-user');
  assert.equal(calls.length,2);
  assert.ok(calls.every(call=>call.cache==='no-store'));
});
test('private file bearer token is restricted to backend storage endpoint',async()=>{
  const calls=[];
  const {api}=loadApi(async(url,init)=>{calls.push(init);return new Response('synthetic document');},{NEXT_PUBLIC_API_URL:'https://api.example.com/api/v1'});
  const local=await api.fetchPrivateFile('/api/v1/storage/resumes/test.pdf');
  URL.revokeObjectURL(local);
  const remote=await api.fetchPrivateFile('https://objects.example.com/test.pdf');
  URL.revokeObjectURL(remote);
  assert.equal(calls[0].headers.Authorization,'Bearer first-user');
  assert.equal(calls[1].headers.Authorization,undefined);
});
test('failed AI analysis does not become a successful null response',async()=>{
  const {api}=loadApi(async()=>new Response('Unavailable',{status:503}));
  await assert.rejects(api.apiService.analyzeResume(),/Resume analysis failed/);
});
