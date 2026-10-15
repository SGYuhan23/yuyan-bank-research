import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const text=readFileSync(new URL('../data/demo-data.json',import.meta.url),'utf8'), data=JSON.parse(text);
test('public payload excludes private context and unused metadata',()=>{
 assert.doesNotMatch(text,/重庆农商行|"disclosure"|"source_fact_ids"|"evidence_type"|"scenario_weight"|credential|\/Users\/|\/mnt\/|working_directory|system_message/i);
 const fields=['id','sector','deposit_fen','annual_transaction_count','payroll_employee_count','eligible_supply_chain_links','relationship_contribution_fen','attrition_scenario'];
 for(const c of [...data.fuling.customers,...data.fuling.comparisons]) assert.deepEqual(Object.keys(c).sort(),fields.slice().sort());
 assert.ok(data.supplier.initial_case.events.length>0);
});
