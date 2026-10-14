"""Curated primary-source evidence register. No inference of bank customer shares."""
import json
from pathlib import Path
base='https://www.fl.gov.cn/zwxx_206/bmfw_20221017q/zpxx/sydwzp/202605/t20260520_15691054.html'
facts=[]
def add(fid,metric,value,period,url,published,usage='background_only',status='官方搜索索引正文读取；原站直读失败，待复核',note=''):
 facts.append(dict(fact_id=fid,metric=metric,value=value,period=period,source=url,source_date=published,retrieved_at='2026-10-13',evidence_type='FACT',model_usage=usage,verification_status=status,limitation=note))
for fid,metric,value in [('FL-GDP','地区生产总值','1783.08亿元'),('FL-GROWTH','GDP可比增长','6.7%'),('FL-IND','规上工业增加值可比增长','9.2%'),('FL-FISCAL','一般公共预算收入','108.00亿元'),('FL-TAX','税收收入','53.65亿元')]:add(fid,metric,value,'2025',base,'2026-05-20')
add('FL-CLUSTERS','公开培育产业方向','先进材料；新能源汽车动力电池及轻量化部件；食品及农产品加工；榨菜','2026页面区情介绍',base,'2026-05-20','scenario_design',note='仅映射客群原型；不映射客户数量、收入或贷款比例。')
add('FL-LOGISTICS','物流定位','西部陆海新通道辅枢纽；龙头港铁公水集疏运中心','2026页面区情介绍',base,'2026-05-20','scenario_design')
add('FL-TRADE','外贸进出口总额','超过150亿元','区情页面未在该句明确统计期',base,'2026-05-20',note='不标作2025精确值，不用于同比或参数输入。')
add('FL-FIRMS','百亿级企业','7户','2026页面区情介绍',base,'2026-05-20',note='不是规上企业总量，更不是银行客户数。规上企业368户仅见二手公报，不纳入事实表。')
add('FL-GAS','页岩气产业链','市能源局与中国石化推进合作，涉及新材料与页岩气产业链','2025-04会议','https://fzggw.cq.gov.cn/zwxx/bmdt/202504/t20250417_14530151_wap.html','2025-04-17','scenario_design')
add('FL-SPECIALIZED','特色产业集群公示','涪陵区页岩气清洁能源产业集群列入拟认定公示','2025公示','https://jjxxw.cq.gov.cn/zwgk_213/gsgg/202506/t20250612_14708109.html','2025-06-12','scenario_design',note='拟认定不等于最终认定；不冒充专精特新企业客户名单。')
add('FL-EXPORT','榨菜出口','3.02万吨；2.66亿元；86个国家和地区','2025','https://wap.cq.gov.cn/zt/yhyshj/zxdt/202606/t20260610_15741283.html','2026-06-10',note='政府网站报道；不等于该产业全部销售额。')
Path(__file__).with_name('fuling_public_facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
# V2 verification: keep only facts backed by saved successful primary-site reads.
records=json.loads((Path(__file__).parent/'evidence-v2/sources/retrieval.json').read_text())
retrieval={r['id']:r for r in records if r.get('status')==200}
facts[:]=[f for f in facts if f['fact_id'] not in {'FL-SPECIALIZED','FL-EXPORT'}]
for f in facts:
 key='fl-gas' if f['fact_id']=='FL-GAS' else 'fl-main'
 r=retrieval[key];f.update(source=r['final_url'],verification_status='已直读官方页面正文并保存文本与SHA256',source_snapshot='evidence-v2/sources/'+key+'.txt',source_sha256=r['sha256'])
 if key=='fl-main':f['limitation']+=' 来源为区政府招募通知附带的区情介绍，并非统计公报；HTTPS失败后读取同官方域名HTTP页面。'
zone=retrieval['fl-zone'];food=retrieval['fl-food']
add('FL-ZONE','经开区规上企业与专精特新企业','规上工业企业115家；国家专精特新“小巨人”8家','页面发布时点：2025-12-26',zone['url'],'2025-12-26','scenario_design','已直读官方页面正文并保存文本与SHA256','仅经开区范围，不外推全区，不等于银行客户数。')
facts[-1].update(source_snapshot='evidence-v2/sources/fl-zone.txt',source_sha256=zone['sha256'])
add('FL-FOOD','榨菜产业覆盖','青菜头74万亩、190万吨；产品远销86个国家和地区','2026-02新闻发布会口径',food['url'],'2026-02-03','scenario_design','已直读官方页面正文并保存文本与SHA256','新闻发布会引述区负责人；非本项目估计。不得据此推导银行客户数。')
facts[-1].update(source_snapshot='evidence-v2/sources/fl-food.txt',source_sha256=food['sha256'])
Path(__file__).with_name('fuling_public_facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
