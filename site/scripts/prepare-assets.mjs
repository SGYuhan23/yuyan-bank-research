import {mkdirSync,cpSync} from 'node:fs';
mkdirSync('public/assets/screenshots',{recursive:true});
cpSync('data','public/data',{recursive:true});
for(const name of ['01-fuling-overview','02-fuling-allocation','03-fuling-customer-action','04-supplier-overview','07-supplier-contract','08-supplier-reconcile']) cpSync(`../docs/screenshots/${name}.png`,`public/assets/screenshots/${name}.png`);
mkdirSync('public/assets/reports',{recursive:true});
cpSync('../docs/reports','public/assets/reports',{recursive:true});
