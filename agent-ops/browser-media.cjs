const {chromium}=require('../agent-platform/frontend/node_modules/@playwright/test');
const fs=require('fs'),path=require('path');
(async()=>{
 const b=await chromium.launch({headless:true});const ctx=await b.newContext({locale:'zh-CN',viewport:{width:1440,height:1000}});
 const a=JSON.parse(fs.readFileSync(path.join(__dirname,'../agent-platform/.deer-flow/acceptance/account.json')));
 const login=await ctx.request.post('http://127.0.0.1:3000/api/v1/auth/login/local',{form:{username:a.email,password:a.password},headers:{Origin:'http://127.0.0.1:3000'}});if(!login.ok())throw Error('login failed');
 const e=JSON.parse(fs.readFileSync(path.join(__dirname,'evidence/media-fdc0cdc0-887a-4d6a-a07f-53a9f6261a69.json')));
 const p=await ctx.newPage();const errors=[];p.on('pageerror',err=>errors.push(err.message));
 await p.goto('http://127.0.0.1:3000/workspace/chats/'+e.thread,{waitUntil:'networkidle',timeout:90000});
 const filename=e.state.values.artifacts.find(x=>x.endsWith('.png')).split('/').pop();
 const link=p.getByText(filename,{exact:true}).first();await link.click();
 await p.waitForTimeout(1800);
 const imgs=await p.locator('img').evaluateAll(xs=>xs.map(x=>({src:x.getAttribute('src'),loaded:x.complete&&x.naturalWidth>0,width:x.naturalWidth})));
 await p.screenshot({path:path.join(__dirname,'evidence/image-preview.png'),fullPage:true});
 console.log(JSON.stringify({thread:e.thread,images:imgs,errors}));
 if(!imgs.some(x=>x.loaded&&x.width>=1024))throw Error('generated image not rendered');
 if(errors.length)throw Error('page errors');
 await b.close();
})();
