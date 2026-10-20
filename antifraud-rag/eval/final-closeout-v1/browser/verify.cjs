const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert');
const out=__dirname,root=path.resolve(__dirname,'../../..'),base=process.env.BASE_URL||'http://127.0.0.1:8792';
(async()=>{
 const b=await chromium.launch({channel:'chrome',headless:true});const p=await b.newPage({viewport:{width:1360,height:1000}});const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto(base);
 // Actual old output rendered in new UI, explicitly a historical fixture, not a model run.
 const old=JSON.parse(fs.readFileSync(path.join(root,'eval/repair-v2/followup-v2/normal-agent-cd1a053d551c43adac28760162a51cb9.json')));
 await p.evaluate(d=>render(d),old);assert((await p.locator('#complete-answer').innerText()).includes('诈骗高发'));
 for(const claim of old.answer.risks)assert((await p.locator('#complete-answer').innerText()).includes(claim.text));
 assert((await p.locator('#review-scope').innerText()).includes('风险线索'));
 await p.screenshot({path:path.join(out,'historical-risk-visible.png'),fullPage:true});
 await p.reload();await p.locator('#query').fill('对方发来转账凭证，货可以给他了吗？我是卖家，附件是买家发来的文字，尚未核对本人银行实际到账。');await p.locator('#case-form button').click();await p.locator('#run').waitFor();
 await p.locator('#upload').setInputFiles({name:'authored-receipt.txt',mimeType:'text/plain',buffer:Buffer.from('本项目编写的演示材料，非真实交易。买家消息：我已经转账，请今天交货。此文字不是银行到账证明。')});
 await p.waitForFunction(()=>document.querySelector('#version').textContent.includes('版本 2'));
 await p.locator('#run').click();await p.locator('#review').waitFor({state:'visible',timeout:300000});
 const result=await p.evaluate(()=>run);fs.writeFileSync(path.join(out,'main-run.json'),JSON.stringify(result,null,2));
 assert.equal(result.status,'pending_review',result.error);assert(result.tool_results.some(t=>t.tool_name==='extract'&&t.status==='ok'));assert(result.tool_results.some(t=>t.tool_name==='guidance'&&t.status==='ok'));
 assert((await p.locator('#complete-answer').innerText()).includes('到账'));assert((await p.locator('#result').locator('a[target="_blank"]').count())>0);
 await p.locator('#operator').fill('automated-browser-verification');await p.locator('#note').fill('自动化界面流程验证：不代表人工业务认可或交易安全，来源复核另附报告。');
 await p.locator('[data-review="revise"]').click();await p.locator('#human-revision').waitFor();assert((await p.locator('#review-status').innerText()).includes('未改写'));
 assert.deepEqual(await p.evaluate(()=>run.answer),result.answer);
 await p.locator('[data-review="accept"]').click();await p.waitForFunction(()=>document.querySelector('#review-status').textContent.includes('完整原始结果'));
 await p.screenshot({path:path.join(out,'main-reviewed.png'),fullPage:true});
 const download=p.waitForEvent('download');await p.locator('#export').click();await (await download).saveAs(path.join(out,'main-export.json'));
 const exported=JSON.parse(fs.readFileSync(path.join(out,'main-export.json')));assert(exported.reviews.every(r=>r.result_hash));
 await p.locator('#query').fill('更正演示材料：买家撤回付款陈述，需要重新研究。');await p.locator('#update').click();await p.locator('#review').waitFor({state:'hidden'});
 const stale=await (await p.request.get(base+'/api/cases/'+result.case_id)).json();assert(stale.results.find(r=>r.run_id===result.run_id).stale);
 const response=await p.request.post(base+'/api/review',{data:{request_id:'stale-'+Date.now(),case_id:result.case_id,case_version:result.case_version,result_id:result.run_id,operator:'automated-browser-verification',decision:'accept',note:'stale regression',revisions:[]}});assert.equal(response.status(),400);
 fs.writeFileSync(path.join(out,'stale-export.json'),JSON.stringify(stale,null,2));
 // Real deterministic graph exercise, no language model planning.
 await p.locator('[data-mode="graph_lab"]').click();await p.locator('#graph-model').selectOption('graphsage');await p.locator('#graph-load').click();await p.locator('#graph-run').waitFor();await p.locator('#graph-run').click();await p.locator('#review').waitFor({state:'visible',timeout:60000});
 const graph=await p.evaluate(()=>run);assert.equal(graph.status,'pending_review');assert.deepEqual(graph.tool_results.map(t=>t.tool_name).sort(),['graph','score']);assert(!graph.records.some(r=>r.kind==='model_call'));assert.equal(graph.graph_exercise.candidates.length,Math.ceil(graph.graph_exercise.accounts*.1));
 fs.writeFileSync(path.join(out,'graph-run.json'),JSON.stringify(graph,null,2));await p.screenshot({path:path.join(out,'graph.png'),fullPage:true});
 fs.writeFileSync(path.join(out,'assertions.json'),JSON.stringify({errors,historical_fixture:'cd1a053d551c43adac28760162a51cb9',historical_full_risks_visible:true,main_run_id:result.run_id,actual_tools:result.tool_results.map(t=>t.tool_name),separate_revision:true,exported:true,stale_rejected:true,graph_run_id:graph.run_id,graph_no_llm:true,scope:'browser automation acceptance is a UI test, not human business approval'},null,2));assert.equal(errors.length,0);await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
