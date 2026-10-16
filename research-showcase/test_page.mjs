import { readFileSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';
const page=process.env.RESEARCH_PAGE||'./渝研_交互研究页面.html';
const html=readFileSync(new URL(page,import.meta.url),'utf8');
const window=new Window({url:'https://example.test/research/'});
window.document.write(html.replace(/<script>([\s\S]*?)<\/script>/g,''));
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
for(const script of scripts)window.eval(script);
const d=window.document,checks=[];
function check(name,fn){fn();checks.push({name,status:'PASS'});}
function click(sel){assert.ok(d.querySelector(sel),sel);d.querySelector(sel).click();}
check('three customer tasks visible without expanding',()=>{assert.equal(d.querySelectorAll('.client').length,3);assert.equal(d.querySelectorAll('#task-table tr').length,3);assert.match(d.querySelector('#client-cards').textContent,/结算覆盖/);assert.equal(d.querySelectorAll('details').length,0);});
check('capacity alternative changes recommendation',()=>{click('[data-capacity="tight"]');assert.match(d.querySelector('#allocation-result').textContent,/2小时订单预检/);click('[data-capacity="missing"]');assert.match(d.querySelector('#allocation-result').textContent,/暂停经销商融资建议/);click('[data-capacity="base"]');});
check('cash ledger switches to actual selected profile',()=>{click('[data-client="F03"]');assert.match(d.querySelector('#client-ledger').textContent,/32万元/);assert.match(d.querySelector('#client-ledger').textContent,/-36/);click('[data-client="F01"]');});
check('tab selection reveals relevant case',()=>{click('[data-tab="supplier"]');assert.equal(d.querySelector('#supplier').hidden,false);assert.equal(d.querySelector('#fuling').hidden,true);});
check('new scenario is not applied before confirmation',()=>{click('[data-scenario="bill"]');assert.equal(d.querySelector('#proposal').hidden,false);assert.match(d.querySelector('#supplier-result').textContent,/94 天/);assert.match(d.querySelector('#proposal').textContent,/尚未确认/);});
check('confirmed parameters bind correct scenario',()=>{click('#confirm-scenario');assert.match(d.querySelector('#supplier-result').textContent,/185 天/);assert.match(d.querySelector('#supplier-result').textContent,/R2/);assert.equal(d.querySelector('#proposal').hidden,true);});
check('cancel keeps previous confirmed result',()=>{click('[data-scenario="late"]');click('#cancel-scenario');assert.match(d.querySelector('#supplier-result').textContent,/185 天/);});
check('discount uses correct net cash and cost',()=>{click('[data-scenario="discount"]');click('#confirm-scenario');assert.match(d.querySelector('#supplier-result').textContent,/6,627.95/);assert.match(d.querySelector('#supplier-result').textContent,/95 天/);assert.equal(d.querySelectorAll('#supplier-result tbody tr').length,5);});
check('all four comparison rows are rendered',()=>assert.equal(d.querySelectorAll('#comparison tr').length,4));
check('seven source links and independent report available',()=>{click('[data-tab="evidence"]');assert.equal(d.querySelectorAll('#sources .source').length,7);const a=d.querySelector('#report-download');if(a.href.startsWith('data:'))assert.equal(Buffer.from(a.href.split(',')[1],'base64').subarray(0,5).toString(),'%PDF-');else{assert.equal(decodeURIComponent(a.getAttribute('href')),'渝研_产业经营研究报告.pdf');assert.equal(readFileSync(new URL('./dist/渝研_产业经营研究报告.pdf',import.meta.url)).subarray(0,5).toString(),'%PDF-');}});
check('no free input or unresolved template tokens',()=>{assert.equal(d.querySelectorAll('input,textarea').length,0);assert.doesNotMatch(html,/__RESEARCH_DATA__|__REPORT_DOWNLOAD__/);});
check('no simulated live model claim',()=>assert.match(d.querySelector('#evidence').textContent,/不现场调用Qwen/));
writeFileSync(new URL(page.includes('dist/')?'./qa/deploy-dom-tests.json':'./qa/dom-tests.json',import.meta.url),JSON.stringify({method:'happy-dom; DOM interaction checks, not browser rendering QA',checks},null,2));
console.log(JSON.stringify(checks,null,2));
await window.happyDOM.close();
