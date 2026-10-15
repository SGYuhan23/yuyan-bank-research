import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {Window} from 'happy-dom';
import {createServer} from 'vite';
const data=JSON.parse(readFileSync(new URL('../../data/demo-data.json',import.meta.url)));
test('page never publishes candidate results rejected by snapshot or version guard',async()=>{
 const window=new Window({url:'http://localhost/'});
 for(const key of ['window','document','navigator','HTMLElement','Element','Node','SVGElement','ShadowRoot','MutationObserver','getComputedStyle'])Object.defineProperty(globalThis,key,{configurable:true,value:key==='window'?window:key==='getComputedStyle'?window.getComputedStyle.bind(window):window[key]});
 window.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});
 globalThis.fetch=async()=>({ok:true,json:async()=>structuredClone(data)});
 const vite=await createServer({root:fileURLToPath(new URL('../..',import.meta.url)),server:{middlewareMode:true,hmr:false},appType:'custom'});
 const React=await import('react'),{createRoot}=await import('react-dom/client'),{MemoryRouter,Routes,Route}=await import('react-router-dom');
 const {default:Page}=await vite.ssrLoadModule('/src/pages/AgentDemo.tsx');
 const {GuidedSession}=await vite.ssrLoadModule('/src/demo/runtime.js');
 const run=GuidedSession.prototype.run;
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 const waitFor=async(predicate,message)=>{const deadline=Date.now()+10000;while(!predicate()){assert.ok(Date.now()<deadline,message);await sleep(25);}};
 try{for(const failure of ['snapshot','version']){
  let produced=false,session;GuidedSession.prototype.run=function(){session=this;const r=run.call(this);produced=true;if(failure==='snapshot')r.snapshot.parameters.delay_days=30;else r.value.scenario.base_version++;return r;};
  const host=document.createElement('div');document.body.append(host);const root=createRoot(host);let published=false;
  const observer=new MutationObserver(()=>{if(host.querySelector('[data-testid="tool-result"]'))published=true;});observer.observe(host,{childList:true,subtree:true});
  root.render(React.createElement(MemoryRouter,{initialEntries:['/demo/cashflow']},React.createElement(Routes,null,React.createElement(Route,{path:'/demo/:id',element:React.createElement(Page)}))));
  const confirmButton=()=>[...host.querySelectorAll('button')].find(b=>b.textContent==='确认并计算');
  await waitFor(()=>confirmButton()&&!confirmButton().disabled,'confirmation button becomes ready');confirmButton().click();
  await waitFor(()=>produced&&/请重新确认/.test(host.textContent),'rejected candidate requires confirmation again');
  assert.ok(produced,'tool produced a candidate');assert.equal(published,false,'ToolResult never entered DOM, including before guard');assert.equal(host.querySelector('[data-testid="tool-result"]'),null);assert.match(host.textContent,/请重新确认/);assert.equal(session.binding.confirmed,false);assert.ok(!host.querySelector('.metrics'));
  observer.disconnect();root.unmount();host.remove();
 }}finally{GuidedSession.prototype.run=run;await vite.close();window.happyDOM.abort();}
});
