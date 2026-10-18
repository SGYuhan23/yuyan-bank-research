from pathlib import Path
import re,json,hashlib,datetime
ROOT=Path(__file__).resolve().parent
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def between(s,a,b):return s[s.index(a):s.index(b,s.index(a)+len(a))].strip()
def cleanweb(s):
 s=re.sub(r'cite\d+†([^†]+)(?:†[^]+)?',r'\1',s)
 return re.sub(r'L\d+: ?', '',s).strip()
raw=(ROOT/'data/raw/web-extract.txt').read_text();parts=raw.split('--------------------------------------------------------------------------------')
case=cleanweb(between(parts[0],'L30:','L46:'))
stats=cleanweb(between(parts[1],'L38:','L88:'))
a=(ROOT/'data/raw/asic-section-web.txt').read_text();asic=cleanweb(between(a,'L401:','L437:'))
w=(ROOT/'data/raw/westpac-bec.txt').read_text();receipt=(ROOT/'data/raw/westpac-receipt.txt').read_text()
index=json.loads((ROOT/'data/source-index.json').read_text());lookup={s['source_id']:s for s in index}
for sid,title,url,kind,text in [
 ('scamwatch-case','False billing: John updated supplier details and it ended up costing thousands','https://www.scamwatch.gov.au/stop-check-protect/real-life-stories/false-billing-john-updated-supplier-details-and-it-ended-up-costing-thousands','official_public_case',case),
 ('scamwatch-stats','Targeting scams report — 2025 infographic','https://www.scamwatch.gov.au/research-and-resources/targeting-scams-report','official_statistics',stats),
 ('asic-invest','Check before you invest','https://moneysmart.gov.au/check-and-report-scams/check-before-you-invest','official_guidance',asic)]:
  path=ROOT/'data/raw'/f'{sid}-web-section.txt';path.write_text(text)
  lookup[sid]=dict(source_id=sid,title=title,url=url,material_type=kind,published_or_updated_at='2026-03-30' if sid.endswith('stats') else None,date_status='report_publication_date' if sid.endswith('stats') else 'not_shown_in_read_section',retrieved_at=now,region='Australia',file_sha256=sha(path.read_bytes()),hash_scope='saved_web_tool_section_not_original_html',acquisition_method='web_tool_original_url_extraction_after_direct_http_403',seed_provenance='independently_discovered_material_pack_missing')
units=[]
def unit(uid,sid,section,text,tags,limits):
 s=lookup[sid];s['review_status']='codex_author_checked_pending_independent_review';s['page_or_section']=section;s.setdefault('hash_scope','original_http_html');s.setdefault('acquisition_method','httpx')
 if sid=='westpac-receipt':s['section_date']='2023-04';s['date_status']='page_update_not_shown_section_dated_2023_04'
 units.append(dict(unit_id=uid,**s,section=section,text=text,search_labels=tags,limitations=limits,limitations_origin='project_author_scope_note_not_official_quote',unit_sha256=sha(text.encode())))
unit('bec-guidance','westpac-bec','Signs this may be a scam + Tips to minimise the risk',between(w,'Signs this may be a scam','Examples of scams*')+'\n\n'+between(w,'Tips to minimise the risk of being scammed','What you can do if you'), '供应商 收款账户变更 更换 银行 邮件 发票 核实 电话 紧急 客服 培训 invoice supplier account change verify','公开一般安全建议，非Westpac内部操作规程；账户变更是核实信号，不足以证明欺诈。PayID和双人审批以可用为条件。')
unit('bec-case','scamwatch-case','Complete John case, privacy caveat and response',case,'供应商 收款账户变更 官方 案例 John 培训 supplier account change case','官方基于一个或多个真实举报编写，姓名图像已处理；不是本项目客户案例，不能估计客户损失。')
unit('receipt-guidance','westpac-receipt','April 2023 - PayID Scam',between(receipt,'April 2023 - PayID Scam','March 2023 - LinkT Scams'),'付款截图 收据 到账 网银 卖货 交货 receipt screenshot payment funds','2023年4月公开提示，场景为网上出售物品；不能据此判定某笔交易已经到账或已构成诈骗。')
unit('investment-check','asic-invest','CHECK: Is the company/person real and licensed or authorised — full section and table',asic,'投资 邀约 专业网页 机构登记 注册 公司 牌照 ASIC 真实 安全 website registration investment licence','适用澳大利亚投资核验；注册不等于获许可，获许可不等于投资安全或ASIC认可。')
unit('national-statistics','scamwatch-stats','2025 Infographic: Losses and top-five tables for 2025/2024',stats,'全国 举报 统计 损失 数据 Westpac 客户 风险 2025 2024 增长 比例 reports statistics losses','全国多机构合并举报口径，不是Westpac客户样本；不能推算单个客户风险。页面历史总额有四舍五入，不能用它重算精确同比。')
# Project recommendations never enter the official retrieval index.
research=dict(source_id='project-boundaries',title='本项目资料解释与使用边界',url=None,published_or_updated_at='2026-10-18',retrieved_at=now,region='Australia public-education prototype',material_type='project_research_recommendation',page_or_section='scope',review_status='author_draft_pending_human_review',text='正规供应商可能合法变更账户，应核实请求而非仅凭变更定性。全国举报统计没有客户个体风险分母。公开指引不能取代银行内部政策。')
research['file_sha256']=sha(research['text'].encode());research['hash_scope']='text_field'
(ROOT/'data/research/boundaries.json').write_text(json.dumps(research,ensure_ascii=False,indent=2))
(ROOT/'data/source-index.json').write_text(json.dumps(list(lookup.values()),ensure_ascii=False,indent=2))
(ROOT/'data/units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2))
for kind in {u['material_type'] for u in units}:
 (ROOT/'data'/f'{kind}.json').write_text(json.dumps([u for u in units if u['material_type']==kind],ensure_ascii=False,indent=2))
print('Prepared',len(units),'complete retrieval units; research/training excluded')
