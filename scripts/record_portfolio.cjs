/** Actual local browser recording. No mocked requests, DOM rewriting or model calls.
 * ACCOUNT_FILE points to an ignored local synthetic demonstration account.
 * Raw recordings include the sidebar: keep them in ignored tmp; publish only cropped exports.
 */
const {chromium}=require('../agent-platform/frontend/node_modules/@playwright/test');
const fs=require('fs'),path=require('path');
const origin=process.env.DEMO_ORIGIN||'http://127.0.0.1:3002';
const accountFile=process.env.ACCOUNT_FILE||'agent-platform/.deer-flow/acceptance/account.json';
const screenshots='docs/screenshots',rawDir='tmp/portfolio-recordings';
fs.mkdirSync(screenshots,{recursive:true});fs.mkdirSync(rawDir,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const browser=await chromium.launch();const account=JSON.parse(fs.readFileSync(accountFile));
 const audit={origin:'local loopback only',date:'2026-10-14',mocked_requests:false,dom_content_modified:false,new_model_call:false,recordings:[],screenshots:[],checks:{}};
 async function session(name,work,minSeconds){
  const context=await browser.newContext({viewport:{width:1500,height:1000},locale:'zh-CN',colorScheme:'light',recordVideo:{dir:rawDir,size:{width:1500,height:1000}}});
  const login=await context.request.post(origin+'/api/v1/auth/login/local',{form:{username:account.email,password:account.password},headers:{Origin:origin}});
  if(!login.ok())throw Error('Local login failed: '+login.status());
  const p=await context.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
  const started=Date.now();await p.goto(origin+'/workspace/research',{waitUntil:'networkidle'});
  await p.getByRole('heading',{name:'先理解业务，再讨论决策',exact:true}).waitFor();
  const scroll=p.locator('#research-scroll');
  async function top(){await scroll.evaluate(e=>e.scrollTo({top:0,behavior:'instant'}));await sleep(350)}
  async function show(name){await p.getByRole('heading',{name,exact:true}).evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));await sleep(450)}
  async function shot(name){await scroll.screenshot({path:path.join(screenshots,name+'.png')});audit.screenshots.push(name)}
  const tab=async name=>{await top();await p.getByRole('button',{name,exact:true}).click();await top()};
  await work({p,top,show,shot,tab,scroll});
  const remaining=minSeconds*1000-(Date.now()-started);if(remaining>0)await sleep(remaining);
  if(errors.length)throw Error('Browser error: '+errors.join(';'));
  const video=p.video();await context.close();const file=await video.path();const dest=path.join(rawDir,name+'.webm');fs.renameSync(file,dest);
  audit.recordings.push({name,seconds:Number(((Date.now()-started)/1000).toFixed(2)),page_errors:0,sidebar_crop:{x:256,y:0,width:1244,height:1000}});
  fs.writeFileSync('docs/media/capture-evidence.json',JSON.stringify(audit,null,2));console.log(name+' actual browser recording completed');
 }
 await session('overview',async({p,top,show,shot,tab})=>{
  await p.getByText('订单最终回款覆盖列示支出，为什么过程中仍可能出现现金缺口？',{exact:true}).waitFor();await shot('00-overview');await sleep(5000);
  await tab('Case A · 涪陵');await sleep(5000);
  await tab('Case B · 供应商');await p.getByRole('button',{name:'创建独立合成案例',exact:true}).click();await p.getByText('关键材料核对：',{exact:false}).waitFor();await sleep(5000);
  await tab('研究总览');await show('三个角色，三种责任');await sleep(7000);
  await show('一条真实研究助手调用');await shot('10-trace');await sleep(9000);
  await top();
 },48);
 await session('fuling',async({p,top,show,shot,tab})=>{
  await tab('Case A · 涪陵');await shot('01-fuling-overview');await sleep(9000);
  await show('02 / 有限资源，先做哪些任务？');await p.getByLabel('资源与集中度情景').selectOption('0');await sleep(9000);
  await p.getByLabel('资源与集中度情景').selectOption('2');await p.getByText('45,027元',{exact:false}).first().waitFor();await sleep(10000);
  await p.getByLabel('资源与集中度情景').selectOption('3');await p.getByText('44,205元',{exact:false}).first().waitFor();await shot('03-fuling-customer-action');await sleep(12000);
  await show('03 / 约束到底改变了什么？');await shot('02-fuling-allocation');await sleep(12000);
  audit.checks.fulingFourAllocationScenarios=true;
 },68);
 await session('supplier-ai',async({p,top,show,shot,tab,scroll})=>{
  await tab('Case B · 供应商');await p.getByRole('button',{name:'创建独立合成案例',exact:true}).click();await p.getByText('关键材料核对：',{exact:false}).waitFor();await shot('04-supplier-overview');await sleep(3500);
  await p.getByText('关键材料核对：',{exact:false}).evaluate(e=>e.closest('section').scrollIntoView({block:'start'}));await sleep(350);await shot('05-supplier-cashflow');await sleep(4500);
  await show('02 / 比较未落实条款');await shot('07-supplier-contract');await sleep(5000);
  await p.getByRole('button',{name:'校验并回显情景参数',exact:true}).click();await p.getByRole('button',{name:'确认参数并计算',exact:true}).click();await p.getByText('38 → 52天',{exact:false}).waitFor();await show('02 / 比较未落实条款');await shot('09-agent-scenario');await sleep(7000);
  await p.getByLabel('延期天数',{exact:true}).fill('30');if(await p.getByText('38 → 52天',{exact:false}).count())throw Error('Old scenario not invalidated');await p.getByLabel('影响客户').selectOption('ALL');await sleep(2000);
  await p.getByRole('button',{name:'校验并回显情景参数',exact:true}).click();await p.getByRole('button',{name:'确认参数并计算',exact:true}).click();await p.getByText('38 → 68天',{exact:false}).waitFor();await sleep(4500);
  await show('03 / 核对事件与变更');await shot('06-supplier-ledger');await sleep(4500);
  await p.getByLabel('事件',{exact:false}).selectOption('O1-materials');await p.getByLabel('操作',{exact:true}).selectOption('confirm');await p.getByLabel('原因',{exact:true}).fill('公开作品演示：合成付款确认');await p.getByLabel('凭证/来源说明').fill('合成合同，仅供演示');await p.getByRole('button',{name:'预览变更',exact:true}).click();await p.getByRole('button',{name:'明确确认并提交',exact:true}).click();await p.getByText('版本 2',{exact:false}).first().waitFor();
  await p.getByLabel('操作',{exact:true}).selectOption('record_actuals_and_reconcile');await p.getByLabel('日期',{exact:true}).fill('2027-01-08');await p.getByLabel('新核对边界（当天00:00，不含）').fill('2027-01-09');await p.getByLabel('观察到的实际余额/元').fill('0');await sleep(3500);
  await p.getByRole('button',{name:'预览变更',exact:true}).click();await p.getByRole('button',{name:'明确确认并提交',exact:true}).click();await p.getByRole('alert').filter({hasText:'全部回滚'}).waitFor();await top();await shot('08-supplier-reconcile');await p.getByText('版本 2',{exact:false}).first().waitFor();await sleep(6000);
  await p.getByLabel('观察到的实际余额/元').fill('-100000');await p.getByRole('button',{name:'预览变更',exact:true}).click();await p.getByRole('button',{name:'明确确认并提交',exact:true}).click();await p.getByText('版本 3',{exact:false}).first().waitFor();await top();await sleep(5000);
  audit.checks={...audit.checks,C1_14_confirmed:true,changedInputInvalidatesOldResult:true,ALL_30_distinct:true,mismatchRolledBackVersion2:true,matchedActualCommittedVersion3:true};
 },78);
 await browser.close();console.log('All captures use real local UI; no model response fabricated.');
})().catch(e=>{console.error(e.message);process.exit(1)});
