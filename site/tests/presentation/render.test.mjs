import test from 'node:test';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createServer} from 'vite';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {MemoryRouter} from 'react-router-dom';
import {GuidedSession} from '../../src/demo/runtime.js';
const data=JSON.parse(readFileSync(new URL('../../data/demo-data.json',import.meta.url)));
test('presentation renders four guided scenarios and real per-scenario trace',async()=>{
 const vite=await createServer({root:fileURLToPath(new URL('../..',import.meta.url)),server:{middlewareMode:true},appType:'custom'});
 try {
 const render=(C,props={})=>renderToStaticMarkup(React.createElement(MemoryRouter,null,React.createElement(C,props)));
 const {default:Landing}=await vite.ssrLoadModule('/src/pages/Landing.tsx');
 const landing=render(Landing); assert.match(landing,/为什么不能让 AI 直接给答案/);assert.match(landing,/银行经营分析 Agent/); assert.doesNotMatch(landing,/研究的是理解、计算与决策的边界/);
 const {scenarios}=await vite.ssrLoadModule('/src/demo/scenarios.ts'); assert.deepEqual(scenarios.map(s=>s.id),['allocation','customer','cashflow','reconcile']);
 const {default:Trace}=await vite.ssrLoadModule('/src/components/AgentTrace.tsx');
 const {default:Result}=await vite.ssrLoadModule('/src/components/ToolResult.tsx');
 for(const s of scenarios){const session=new GuidedSession(data,s.id);
 const waiting=render(Trace,{session,step:2,busy:false,output:null,trace:null,recorded:false});
 assert.match(waiting,/等待用户确认/);assert.doesNotMatch(waiting,/✓ 已收到用户确认/);assert.match(waiting,/Agent 执行轨迹/);
 session.confirm();const output=session.run(); const done=render(Trace,{session,step:5,busy:false,output,trace:null,recorded:false})+render(Result,{id:s.id,output});
 assert.match(done,/参数快照与本次问题一致/);assert.doesNotMatch(done.replace(/<[^>]*>/g,""),/SYN-V2|重庆农商行/);assert.doesNotMatch(done,/<textarea|type="submit"/);
 }
 const {ScenarioComposer}=await vite.ssrLoadModule('/src/components/AgentChat.tsx'); assert.doesNotMatch(render(ScenarioComposer),/<textarea|<input|type="submit"/);
 assert.match(readFileSync(new URL('../../../README.md',import.meta.url),'utf8'),/https:\/\/sgyuhan23.github.io\/yuyan-bank-research\//);
 }finally{await vite.close();}
});
