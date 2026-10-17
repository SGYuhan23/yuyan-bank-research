"""Build a static, source-checked research replay. No model/network calls are made.
Facts and judgement are authored inputs, never reported as autonomous discovery.
"""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json, hashlib
from datetime import datetime, timezone
from research_playbook import PLAYBOOK
ROOT=Path(__file__).resolve().parent

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def norm(s): return ''.join(s.split())

def build():
    sources={s['source_id']:s for s in json.loads((ROOT/'data/sources.json').read_text())}
    facts={f['fact_id']:f for f in json.loads((ROOT/'data/reference-facts.json').read_text())}
    companies=json.loads((ROOT/'data/companies.json').read_text())
    bundle={'mode':'author_checked_fixed_workflow','coverage_date':'2026-10-18','companies':[],'sources':sources}
    trace=[]
    for company in companies:
        cid=company['company_id']; policy=PLAYBOOK[cid]; versions=[]
        for index,(label,ids) in enumerate(policy['versions']):
            selected=[facts[i] for i in ids]
            for f in selected:
                assert f['company_id']==cid, 'Wrong legal entity'
                s=sources[f['source_id']]
                assert any(norm(f['excerpt']) in norm(x['text']) and x['page_or_section']==f['page_or_section'] for x in s['sections']), f['fact_id']
            canonical=sorted({sources[f['source_id']]['canonical_source_id'] for f in selected})
            calculations=[]
            def calc(fid,a,b,label,formula,unit,kind='growth'):
                f=facts[fid]; values=f['values']; x=Decimal(values[a]); y=Decimal(values[b])
                assert y!=0
                result=((x/y if kind=='ratio' else (x-y)/y)*100).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
                calculations.append(dict(fact_id=fid,label=label,inputs=[str(x),str(y)],input_unit=unit,formula=formula,result=str(result),unit='%',period=f['period']))
            if 'R2' in ids: calc('R2','environment_wan','planned_investment_wan','环保投资占计划投资','30 ÷ 553 × 100','万元','ratio')
            if 'Q1' in ids: calc('Q1','revenue_2025','revenue_2024','2025年度合并收入同比','(1352249546.74 − 1599923214.87) ÷ 1599923214.87 × 100','人民币元')
            if 'Q6' in ids: calc('Q6','revenue_2026h1','revenue_2025h1','2026半年合并收入同比','(705550828.01 − 675374807.79) ÷ 675374807.79 × 100','人民币元')
            if 'L1' in ids: calc('L1','revenue_2025','revenue_2024','2025年度合并收入同比','(19135154464.95 − 16822240957.81) ÷ 16822240957.81 × 100','人民币元')
            # Fixed author policy is exposed; no language-model output is claimed here.
            last=index==len(policy['versions'])-1
            h={'title':policy['angle'],'status':'insufficient' if cid in ['qinan-cast','zishuo'] else 'to_verify',
               'reasoning_summary':policy['why'] if last or cid!='loncin' else '只有收入数据，不足以判断跨境结算服务方向。先补读业务和结算章节。',
               'supporting_evidence':[i for i in policy['support'] if i in ids],
               'counter_evidence':[i for i in policy['counter'] if i in ids],
               'missing_information':policy['missing'],'questions_to_verify':policy['questions'],'condition':policy['condition']}
            events=[]
            for f in selected:
                if sources[f['source_id']]['kind']!='primary': continue
                prior=[e['event_id'] for e in events if f['project_id'] and e['project_id']==f['project_id']]
                events.append(dict(event_id=f['fact_id'],company_id=cid,project_id=f['project_id'],event_date=f['event_date'],published_at=f['published_at'],stage=f['stage'],source_ids=[f['source_id']],supersedes=prior[-1:],conflicts=[]))
            version={'label':label,'summary':policy['summary'][min(index,len(policy['summary'])-1)],'facts':selected,'events':events,'calculations':calculations,'hypothesis':h,
                     'canonical_sources':canonical,'excluded_judgement':policy['reject'] if last else '当前范围不足以形成融资需求结论；保持待核实。',
                     'delta':{'added_fact_ids':[i for i in ids if index and i not in policy['versions'][index-1][1]],'replaced_current_stage':[e['supersedes'] for e in events if e['supersedes']], 'explanation':policy['change'] if index else '初始资料范围；不包含后续补读。'},
                     'next_search':policy['next_search']}
            version['evidence_version']=digest({'company':company,'policy':policy,'version':version,'sources':{f['source_id']:sources[f['source_id']] for f in selected}})
            steps=[('确定范围',f"{company['legal_name']}；限定所列资料，不是最新全网覆盖"),('校验原文',f'{len(selected)}条已核校事实与来源快照逐字匹配'),('核对主体与去重',f'{len(canonical)}个规范来源组；集团与子公司不混用'),('确定性计算',f'{len(calculations)}项Decimal计算；保留期间及单位'),('应用作者研究规则','服务方向只作为待核实假设；不足时停止'),('生成版本',version['evidence_version'])]
            version['steps']=[{'step':a,'result':b,'executor':'deterministic_build','at':datetime.now(timezone.utc).isoformat()} for a,b in steps]
            trace.append({'company_id':cid,'evidence_version':version['evidence_version'],'steps':version['steps']})
            versions.append(version)
        bundle['companies'].append({'company':company,'angle':policy['angle'],'versions':versions})
    # Only public evidence snippets; no credentials, environment or internal model thoughts.
    (ROOT/'demo/data.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2))
    (ROOT/'demo/build-trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2))
    archives = {'rifa':'rifa-live-v2', 'qinan':'qinan-v3', 'qinan-cast':'eval-qinan-cast-agent', 'loncin':'loncin', 'zishuo':'eval-zishuo-agent'}
    replays = {cid: {'archive': name, **json.loads((ROOT/'runs'/name/'run.json').read_text())} for cid, name in archives.items()}
    (ROOT/'demo/replays.json').write_text(json.dumps(replays,ensure_ascii=False,indent=2))
    return bundle
if __name__=='__main__':
    data=build(); print(f"Built {len(data['companies'])} companies / {sum(len(c['versions']) for c in data['companies'])} reviewed versions; model calls: 0")
