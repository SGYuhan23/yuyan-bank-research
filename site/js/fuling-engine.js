// Exact grouped knapsack; Map insertion order mirrors Python dict tie-breaking.
export function optimize(actions,hours,cap=null){
 if(!Number.isInteger(hours)||hours<0||hours>1200)throw Error('工时须为0至1200的整数');const ratio=cap??1;if(!(ratio>0&&ratio<=1))throw Error('行业比例须在0与1之间');
 if(new Set(actions.map(a=>a.id)).size!==actions.length)throw Error('任务编号重复');
 const sectors=[...new Set(actions.map(a=>a.sector))].sort(),budget=Math.floor(hours/5),curves=new Map();
 for(const sector of sectors){const groups=new Map();for(const a of actions){if(!Number.isInteger(a.service_hours)||a.service_hours<=0||a.service_hours%5)throw Error('工时需为5小时单位');if(a.sector===sector){if(!groups.has(a.customer_id))groups.set(a.customer_id,[]);groups.get(a.customer_id).push(a);}}
  let dp=new Map([[0,[0,[]]]]);for(const group of groups.values()){const next=new Map(dp);for(const[h,[value,ids]]of dp)for(const a of group){const nh=h+a.service_hours/5,nv=value+a.benefit_fen;if(nh<=budget&&nv>(next.get(nh)?.[0]??-Infinity))next.set(nh,[nv,[...ids,a.id]]);}dp=next;}curves.set(sector,dp);
 }
 let best=[0,[]],used=0;for(let total=1;total<=budget;total++){const limit=Math.floor(total*ratio);let dp=new Map([[0,[0,[]]]]);for(const sector of sectors){const next=new Map();for(const[h,[v,ids]]of dp)for(const[sh,[sv,sids]]of curves.get(sector)){const nh=h+sh;if(sh<=limit&&nh<=total&&v+sv>(next.get(nh)?.[0]??-Infinity))next.set(nh,[v+sv,[...ids,...sids]]);}dp=next;}const candidate=dp.get(total);if(candidate&&candidate[0]>best[0]){best=candidate;used=total*5;}}
 const selected=new Set(best[1]);return{capacity_hours:hours,hours:used,benefit_fen:best[0],selected:best[1],sector_hours:Object.fromEntries(sectors.map(s=>[s,actions.filter(a=>selected.has(a.id)&&a.sector===s).reduce((n,a)=>n+a.service_hours,0)]))};
}
export function valueActions(customer,templates){
 const r=customer,rate=String(r.attrition_scenario),[whole,fraction='']=rate.split('.'),den=10n**BigInt(fraction.length),num=BigInt(whole+fraction);
 const halfUp=(n,d)=>Number((n*2n+d)/(2n*d));
 const gross=[r.annual_transaction_count*60,halfUp(BigInt(r.deposit_fen)*3n,1000n),r.payroll_employee_count*1200,r.eligible_supply_chain_links*28000,halfUp(BigInt(r.relationship_contribution_fen)*num*2n,den*5n)];
 return templates.slice(0,5).map((a,i)=>({...a,id:r.id+'-A'+i,customer_id:r.id,sector:r.sector,expected_benefit_fen:gross[i],benefit_fen:gross[i]-a.implementation_cost_fen,business_drivers:Object.fromEntries(['deposit_fen','annual_transaction_count','payroll_employee_count','eligible_supply_chain_links','relationship_contribution_fen','attrition_scenario'].map(k=>[k,r[k]]))}));
}
