export function chart(container,base,result,label){
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 760 310');svg.setAttribute('role','img');svg.setAttribute('aria-label','基准与情景逐日现金余额，可触摸或悬停查看数值');
 const all=[...base.series,...result.series],dates=[...new Set(all.map(p=>p.date))].sort(),vals=all.map(p=>p.balance_fen),lo=Math.min(0,...vals),hi=Math.max(0,...vals),span=hi-lo||1;
 const x=d=>60+dates.indexOf(d)/(dates.length-1||1)*670,y=v=>245-(v-lo)/span*210;
 function elem(tag,attrs,text){const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;svg.append(e);return e;}
 elem('line',{x1:60,x2:730,y1:y(0),y2:y(0),stroke:'#a9b5c4','stroke-dasharray':'4 4'});
 for(const v of [hi,0,lo])elem('text',{x:4,y:y(v)+4,'font-size':12,fill:'#687789'},(v/1000000).toFixed(1)+'万');
 const tip=document.createElement('p');tip.className='chart-tip';tip.textContent='悬停或触摸曲线点，查看日期与当日余额。';
 [[base,'#8b98a7','基准'],[result,'#155da2',label]].forEach(([r,color,name])=>{elem('path',{d:r.series.map((p,i)=>(i?'L':'M')+x(p.date)+','+y(p.balance_fen)).join(' '),fill:'none',stroke:color,'stroke-width':2.5});for(const p of r.series){const dot=elem('circle',{cx:x(p.date),cy:y(p.balance_fen),r:4,fill:color,opacity:.2,tabindex:0});const text=name+' · '+p.date+' · '+(p.balance_fen/100).toLocaleString('zh-CN')+' 元';const title=document.createElementNS(ns,'title');title.textContent=text;dot.append(title);for(const event of ['mouseenter','focus','pointerdown'])dot.addEventListener(event,()=>{tip.textContent=text;dot.setAttribute('opacity','1');});dot.addEventListener('mouseleave',()=>dot.setAttribute('opacity','.2'));}});
 elem('text',{x:60,y:280,'font-size':12,fill:'#687789'},dates[0]);elem('text',{x:640,y:280,'font-size':12,fill:'#687789'},dates.at(-1));
 const legend=document.createElement('p');legend.className='muted';legend.textContent='灰线：基准场景　蓝线：'+label;container.append(legend,svg,tip);
}
