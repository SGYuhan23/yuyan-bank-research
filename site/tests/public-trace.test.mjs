import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
test('canonical recorded trace matches current question and excludes private context',()=>{
 const text=readFileSync(new URL('../data/traces/supplier.json',import.meta.url),'utf8'),trace=JSON.parse(text);
 assert.doesNotMatch(text,/FINAL-P0-TRACE|CASE-A|REQUEST-A|acceptance_harness|\/Users\/|C:\\|\/mnt\/|API_KEY|credential|system_message|working_directory|skill_system|hidden.reasoning/i);
 assert.deepEqual(Object.keys(trace).sort(),['status','model','recorded_at','actual_user_prompt','context_summary','original_model_proposal','validation_summary','correction_applied','confirmed_request','confirmation_summary','tool','arguments','result','answer','boundary','redaction_note'].sort());
 const source=readFileSync(new URL('../src/demo/scenarios.ts',import.meta.url),'utf8'),question=source.match(/id: "cashflow"[\s\S]*?question:\s*"([^"]+)"/)[1];
 assert.equal(trace.actual_user_prompt.replace(/\s+/g,''),question.replace(/\s+/g,''));assert.equal(trace.status,'verified');
 assert.equal(trace.original_model_proposal.request.customer_id,'C1');assert.equal(trace.original_model_proposal.request.delay_days,14);
 assert.equal(trace.confirmed_request.request.confirmation_status,'CONFIRMED');assert.equal(trace.result.scenario.negative_days,52);
});
