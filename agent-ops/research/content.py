"""V2 manuscripts: shared verified facts and deterministic outputs, no hand-copied results."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=json.loads((ROOT/'agent-platform/frontend/public/research/v2.json').read_text())
facts=DATA['fuling']['facts'];alloc=DATA['fuling']['allocations'];actions=DATA['fuling']['actions'];base=DATA['supplier']['base'];late=DATA['supplier']['delay14']
DATA['sources']=[{'id':'FL','title':'涪陵区政府招募通知附区情介绍','url':facts[0]['source'],'published':facts[0]['source_date'],'period':'2025及页面时点','accessed':'2026-10-13','status':'官方HTTP正文已读取，HTTPS访问失败；附录保留文本与哈希','use':'区域事实与产业原型，不校准金融参数'}, {'id':'ZONE','title':'涪陵经济技术开发区介绍','url':facts[-2]['source'],'published':facts[-2]['source_date'],'period':'页面发布时点，仅园区范围','accessed':'2026-10-13','status':'官方正文已读取并保存','use':'规上企业与专精特新背景'}, {'id':'FOOD','title':'涪陵榨菜产业博览会新闻发布会','url':facts[-1]['source'],'published':facts[-1]['source_date'],'period':facts[-1]['period'],'accessed':'2026-10-13','status':'政府站正文已读取，报道引述区负责人','use':'农业产业链背景'}]
DATA['sources']+=json.loads((Path(__file__).parent/'sources.json').read_text())
def wan(v):return f'{v/1000000:,.2f}'
def money(v):return f'{v/100:,.2f}元'
def page(title,lead,paras=(),table=None,chart=None,note=None):return dict(title=title,lead=lead,paras=list(paras),table=table,chart=chart,note=note)
def table(headers,rows):return dict(headers=headers,rows=rows)
def strategies(stress):return []
def groups(a):
 selected=[x for x in actions if x['id'] in a['selected']]
 return [[k,str(sum(x['action_type']==k for x in selected)),str(sum(x['service_hours'] for x in selected if x['action_type']==k)),money(sum(x['benefit_fen'] for x in selected if x['action_type']==k))] for k in dict.fromkeys(x['action_type'] for x in actions)]
fuling=[
page('管理摘要：先验证机会，再分配资源','DECISION / 正常与受限资源下，任务优先级必须接受成本与分散约束。',[
'这是一项独立经营研究，不代表任何银行官方项目。公开产业事实用于提出待验证问题，120户合成客户用于检验资源配置方法。',
f"在600小时预算下，无行业限额的假设净贡献为{money(alloc[0]['benefit_fen'])}；压缩到150小时后为{money(alloc[2]['benefit_fen'])}。再加入单行业工时不超过实际选中工时25%的限制，净贡献变为{money(alloc[3]['benefit_fen'])}。这些是合成实验结果，不是预测。",
'优先核实结算频次、日均沉淀、接入成本与客户意愿；不依据产业规模直接推导授信额度或客户占比。资源安排只涉及增量经营动作，不挤占预留的必要维护。']),
page('区域事实：经济与公共财力','FACT / 区政府页面附区情介绍；不是本项目估计值。',table=table(['指标','数值','期间/使用边界'],[[f['metric'],f['value'],f['period']+'；仅背景'] for f in facts[:5]]),paras=['原站HTTPS读取失败，已通过同一官方域名HTTP读取正文，保留来源文本、日期和SHA256。页面是招募通知中的区情介绍，不冒充统计公报。','一般公共预算收入与税收不是银行存款、贷款或可用信贷资金。GDP增长也不能直接映射成客户信用改善。']),
page('产业到机会：每一步都需要新证据','FACT → DECISION / 公开产业方向只支持研究问题，不证明需求存在。',table=table(['产业线索','优先核实任务','暂不能下的结论'],[['先进材料/制造业','采购与销售结算周期、上下游授权','产业规模大就应该多贷款'],['新能源及零部件','验收、对账、回款集中时点','所有供应商都有同一账期'],['食品农业/榨菜','采购季节、库存与回款错位','农户数就是银行客户数'],['商贸物流/通道','运费、外贸结算与多式联运支付','港口建设必然带来银行收益'],['小微/居民经营','代发、支付与必要服务维护','未采访也可声称需求已验证']]),paras=['涪陵经开区页面披露规上工业企业115家、国家专精特新“小巨人”8家，仅代表园区范围。榨菜发布会披露74万亩、190万吨和86个国家及地区；这些不进入金融参数。','页岩气链条另有市发改委正文佐证，完整12项事实登记随附件提供；不将拟认定名单当最终认定。']),
page('合成设计与动作经济含义','ASSUMPTION / '+DATA['fuling']['disclosure'].replace('重庆农商行或涪陵', '任何银行或地区'),table=table(['动作','工时','成本/元','业务价值驱动'],[[a['action_type'],a['service_hours'],a['implementation_cost_fen']/100,a['value_formula']] for a in actions[:5]]),paras=['固定随机种子2027，默认五类各24户，可配置权重。行业权重不等于真实市场份额。交易笔数、可授权员工、合格连接、既有关系贡献和情景流失各自驱动价值。单价、采用率、成本和工时全为ASSUMPTION，不是银行参数。','每客户最多选一个动作，避免把同一关系增量在多个动作重复计量；这也简化了现实中的互补效应。正常预算600小时来自3人×1000小时减2100小时维护与300小时合规行政；受限预算另扣450小时排查。均为压力实验。']),
page('真实取舍：工时与集中度一起约束','MODEL OUTPUT / 目标为总假设净贡献最大；可选择不做负贡献动作。',table=table(['产能/限制','使用工时','动作数','净贡献/元'],[[a['name']+(' / 25%上限' if i%2 else ' / 无上限'),a['hours'],len(a['selected']),f"{a['benefit_fen']/100:,.2f}"] for i,a in enumerate(alloc)]),paras=[f"受限产能加集中上限后，净贡献比无上限低{money(alloc[2]['benefit_fen']-alloc[3]['benefit_fen'])}。约束改变了任务组合，而不是只显示一个风险指标。",'上限是实际选中工时的行业份额，不是贷款占比，不是监管或内部限额。求解为分组整数背包与行业组合，最小单位5小时，小规模穷举独立校验。下载数据保留每个未选动作和原因。']),
page('有限工时先给什么任务？','MODEL OUTPUT / 受限150小时、行业25%上限的任务结构。',table=table(['任务','数量','工时','净贡献'],groups(alloc[3])),paras=['选中表示在当前假设下更值得先验证，不是客户评级。未选可能因为净贡献非正、同客户已选替代动作或整体约束下排序较后，不等于停止必要服务。','同余额客户可因交易频次、员工数、合格连接或维护价值而优先不同动作；每个动作随附件列示驱动、工时、成本、待验证材料和停止条件。新能源汽车原型明确映射FL-CLUSTERS，仅借鉴产业方向。']),
page('结论何时失效？','ASSUMPTION → MODEL OUTPUT / 仅折减毛收益，成本照付。',table=table(['收益实现比例','选中任务','使用工时','净贡献'],[[str(int(float(a['realization_rate'])*100))+'%',len(a['selected']),a['hours'],money(a['benefit_fen'])] for a in DATA['fuling']['sensitivity']]),paras=['实现比例不是统计成功概率。该对照用于挑战“账面正贡献即值得做”，收益难实现时应减少或暂停动作，不为排满工时而营销。','执行建议：先核对客户授权、沉淀与服务成本，记录未被选择的替代任务；再小范围验证，更新参数后重新分配。若净贡献转负、必要维护受挤占或客户拒绝授权，应停止扩张。'])]
supplier=[
page('管理摘要：有订单，不等于有可用现金','DECISION / 产品帮助核对资金时点和方案代价，不输出授信承诺。',[
'研究对象是存在采购、生产、发货、验收、开票与账期安排的汽摩供应合同情景。支持这些机制不等于声称它们是所有汽摩企业的普遍条款。未开展真实客户访谈。',
f"合成4笔订单总额96万元，列明支出73万元，订单收支差23万元；期初现金8万元。期初后已录入预付款12万元，因此账本事实余额20万元。预测峰值缺口{wan(base['peak_gap_fen'])}万元、负余额{base['negative_days']}天。订单收支差未含未录入税费等，不称审计利润。",
'用户路径：查看事件与来源 → 定位最低点 → 比较延期/预付/折扣/费用 → 核对确认 → 录入实际收付 → 查看版本与历史。银行接入、授信和支付不在本作品内。']),
page('行业流程：时间与证据比总额更关键','ASSUMPTION / 合成核心订单合同从采购到尾款的可配置节点。',table=table(['节点','作用','现金语义'],[['采购订单','约定交易对象与总额','零金额节点，不重复现金'],['原料/生产/发货','提前占用资金','负数现金事件'],['验收/开票','核对履约与账期条件','零金额节点，可确认或争议'],['回款/预付款','计划日期不等于到账','只有POSTED进入事实余额'],['质量扣款','单独记录异常事件及原因','负数事件；尾款不可再次扣同笔'],['延期/重新协商','形成未落实日期安排','撤销旧确认，回到PROJECTED']]),paras=['合同支持FIXED_DATE与AFTER_INVOICE；后者按验收→开票→N天后回款推导，仅更新PROJECTED日期，绝不自动确认/入账。争议阻断依赖预测，固定日期合同不受验收改期影响。支持条件不推断法律效力。','核心客户订单占比62.5%，Top3为87.5%，分母是合成订单金额，不是银行授信余额。']),
page('状态是真实功能，不是一句风险提示','PROJECTED → CONFIRMED → POSTED / 全部变更保留前后值、原因、时间和版本。',table=table(['状态/操作','事实余额','历史与限制'],[['PROJECTED预测','不进入','可协商日期与金额'],['CONFIRMED已确认安排','不进入','必须有确认日期及证据说明'],['POSTED已录入实际收付','进入一次','不可覆盖、重复入账或取消'],['DISPUTED争议','不作为确定收入','标记结果不完整，需说明依据'],['模拟比较','不修改','不增加账本版本、不保存为基线'],['页面确认提交','依版本事务提交','跨用户拒绝；重试相同键不重复执行']]),paras=['本案例的“事实”仅指合成实验里被标记为已入账的记录，不是连接银行后自动验证的流水。模型只提出参数提案或读取已确认请求；人工核对客户、延期、折扣、费用、预付及版本后才计算。修改输入使旧结果失效，不能用ALL+30天冒充C1+14天。','实际收付与余额一次提交：先在事务副本入账，再按新核对边界核对观察余额；不一致全部回滚并返回差额。核对边界为当天00:00且不含，逾期或争议仍明确标记。']),
page('现金与最低点：独立复算','MODEL OUTPUT / 整数分、逐日累计，曲线含未落实预测。',chart='supplier-cash',table=table(['项目','结果'],[['事实余额',money(base['actual_balance_fen'])],['预测最低点',base['minimum_date']],['峰值缺口',money(base['peak_gap_fen'])],['负余额天数',str(base['negative_days'])],['最低点当天事件','、'.join(base['minimum_drivers'])]]),paras=['日终余额不能保证日内逐笔付款成功。最低点事件解释当日变化，也要结合此前累计支出。结果由事件重算，不由模型填充。','账本金额与现金记录采用整数分，比例用Decimal并明确ROUND_HALF_UP。订单、验收和发票本身不增加现金，避免一项业务多个节点重复计量。']),
page('集中延期：缺口与期限是两种压力','MODEL OUTPUT / 客户订单集中度与回款时点共同观察。',table=table(['情景','峰值缺口/万元','负余额天数'],[[name,wan(x['peak_gap_fen']),x['negative_days']] for name,x in [('基线',base),('核心尾款晚14天',late),('核心客户晚30天',DATA['supplier']['core_customer_stress']),('所有客户同时晚30天',DATA['supplier']['all_customer_stress'])]]),paras=['核心客户延期可能不改变最低点金额，但增加缺口持续时间；多客户同时延期可能进一步恶化最低点。不能只用“缺口有没有变大”判断流动性压力。','预付款只把尾款部分移到较早日期，折扣减少尾款金额，费用在假设发生日计入。改善与代价同屏比较；所有条款都待协商，不意味着已获客户接受。']),
page('关键材料核对与人工判断','产品语义 / 完整性衡量说明是否存在，不衡量信用好坏。',[
f"基准有{base['evidence_completeness']['required']}个关键节点，其中{base['evidence_completeness']['supported']}个有确认说明。订单可确认，但验收、发票和尾款仍需补证；48万元尾款不能视为可用现金。",
'新增事件先进入预测，确认时补日期和凭证；质量扣款独立记录，已入账事实禁止编辑。发现入账错误需人工核对，当前未提供补偿反转与多对多核销，不要用取消预测冒充冲正。',
'面向银行的待验证价值：提高信息整理质量，帮助客户经理识别需要核验的收付时点与材料。尚无真实用户时间节省、客户留存或银行收益数据。试点先观察任务完成率与误解，再决定是否接入真实资料。'])]
d=DATA['deposit']['base']
deposit=[page('扩展研究：存款的边际价值','Experimental Research / 不用于客户定价或真实ALM。',[
'这是简化资金价值实验，FTP、有效资金系数和服务成本全部为研究假设，不代表任何银行内部模型。effective_funding_factor在此只是可用于资金计划的折算系数，不是预测流失概率。',
'公式：年平均余额 ×（有效资金系数 × FTP − 全余额存款利率）− 服务成本。FTP只作用于折算有效资金，利息按全部年平均余额计提。未建资产承诺和流出补足需求，因此删除额外替代资金扣减，避免重复计量。',
f"1000万元×（80%×2%−1.5%）−2万元={wan(d['contribution_fen'])}万元；盈亏平衡利率{float(d['break_even_rate']):.2%}，所需有效资金系数{float(d['break_even_effective_funding_factor']):.2%}。本公式按列示的经济定义计算，不重复扣减资金成本。"]),page('价格与资金有效性共同变化','MODEL OUTPUT / 参数网格不是概率分布或银行报价。',chart='deposit-grid',paras=['颜色仅表示假设贡献正负。资金有效性不足或服务成本较高时，新增余额也可能不创造价值。','集团净息差不是FTP；期末余额不是年平均余额。本模型不含资产收益、资本与流动性约束，不能与涪陵动作收益直接相加。','非零 replacement 参数明确报错，以防重复计算资金成本。'])]
REPORTS=[dict(id='fuling',title='涪陵县域经营分析',subtitle='真实区域事实与合成资源配置实验',tag='主作品 A',summary='有限资源下，先验证哪些经营机会？公开事实给出调研方向，确定性模型展示取舍。',pages=fuling,sources=['FL','ZONE','FOOD']),dict(id='supplier',title='汽摩供应商资金管理',subtitle='事件账本、状态核对与流动性情景',tag='主作品 B',summary='把订单、安排与现金事实分开，比较时点改善、条款代价和未落实条件。',pages=supplier,sources=['P1']),dict(id='deposit',title='存款边际价值：扩展研究',subtitle='明确经济定义后的简化实验',tag='APPENDIX',summary='用条件与阈值解释负债价值，不代替真实FTP、定价或ALM。',pages=deposit,sources=['B1'])]
