"""Independent, synthetic teaching cases. All monetary input/output integers are RMB fen.
The model computes a counterfactual funding-free cash path, not an overdraft account.
"""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).parent
def money(wan):
    return int(Decimal(str(wan))*1_000_000)

def event(id, day, wan, title, basis):
    return dict(id=id, date=day, amount_fen=money(wan), title=title,
                status='PROJECTED', layer='ASSUMPTION', evidence=basis)

def curve(opening, events, start, end):
    start,end=date.fromisoformat(start),date.fromisoformat(end)
    assert start<=end
    ids=[e['id'] for e in events]
    assert len(ids)==len(set(ids)), 'duplicate cash event'
    assert all(start<=date.fromisoformat(e['date'])<=end for e in events)
    flows={}
    for e in events:
        assert type(e['amount_fen']) is int
        flows[e['date']]=flows.get(e['date'],0)+e['amount_fen']
    bal=opening; daily=[]
    for i in range((end-start).days+1):
        day=(start+timedelta(days=i)).isoformat(); bal+=flows.get(day,0)
        daily.append(dict(date=day,balance_fen=bal))
    low=min([opening]+[x['balance_fen'] for x in daily])
    neg=[x for x in daily if x['balance_fen']<0]
    return dict(daily=daily,peak_gap_fen=max(0,-low),min_balance_fen=low,
                negative_days=len(neg),first_gap_date=neg[0]['date'] if neg else None,
                last_gap_date=neg[-1]['date'] if neg else None,end_balance_fen=bal,
                layer='MODEL OUTPUT')

SOURCES=[
dict(id='S1',title='涪陵榨菜集团2025年年度报告',publisher='涪陵榨菜集团／巨潮资讯',date='2026-03-28',
     url='https://static.cninfo.com.cn/finalpage/2026-03-28/1225042838.PDF',locator='报告第10、14页',
     fact='原料集中采购；采购组织涉及合作社与农户；经销结算包括预付款与部分商业授信。',
     use='决定客户原型和资金时点；不提供本案例的客户金额、授信额度或回款保证。'),
dict(id='S2',title='关于2026年青菜头订单种植的公告',publisher='涪陵榨菜集团',date='2025-09-30',
     url='https://www.flzc.com/html/text/f8faf8153b57d456688bd896b80ba5d6.html',locator='订单生产种植条款',
     fact='该企业公告将种植订单作为收购前提。',use='订单存在性须核实；不能据此保证模拟客户可以向该企业销售。'),
dict(id='S3',title='数字赋能促转型，预约收购解民忧',publisher='涪陵榨菜集团',date='2026-03-05',
     url='https://www.flzc.com/html/text/5bd40f8fea2e58cbb167fe7d0d6762f9.html',locator='数据领航、优化不止步',
     fact='企业已有预约收购系统，同时披露交售意向与实际数量可能不一致。',
     use='不重复发明预约平台；核实合同、交售和结算记录是否匹配。'),
dict(id='S4',title='榨菜产业搭上数字化“快车”',publisher='重庆人大',date='2023-10-26',
     url='https://www.cqrd.gov.cn/site/article/1211438449625501696/web/content_1211438449625501696.html',locator='榨菜产业大脑上线',
     fact='报道列举经历约六个月发酵后进入加工环节的生产实例。',
     use='支持跨月资金占用的研究必要性；六个月不是所有产品的标准工期。'),
dict(id='S5',title='2026年半年度业绩说明会',publisher='重庆农商行',date='2026-09-11',
     url='https://www.cqrcb.com/cqrcb/aboutus/presscenter/ourdynamic/335183.html',locator='场景圈动、产业链动',
     fact='该行披露特色产业平台及链式客户经营进展。',use='解释选题相关性；无委托、合作或内部数据关系。'),
dict(id='S6',title='关于推动汽车企业规范供应商账款支付、优化账期管理的通知',publisher='工信部办公厅、市场监管总局办公厅',date='2026-09-07',
     url='https://www.miit.gov.cn/jgsj/zbys/wjfb/art/2026/art_6043f55908f44a71a3e51236f663356b.html',locator='第二部分（一）至（七）',
     fact='文件分别规定验收、账期、支付方式及贴现成本等事项。',
     use='区分合同付款与现金可用；适用主体为文件定义的整车企业，不将其扩展至全部制造业或自动作合规判断。'),
dict(id='S7',title='新能源汽车产业金融服务相关报道',publisher='重庆农商行',date='2025-11-14',
     url='https://www.cqrcb.com/cqrcb/aboutus/presscenter/ourdynamic/333235.html',locator='新能源汽车产业链金融服务',
     fact='该行披露汽车产业链及零部件企业服务实践。',use='选题背景；不代表模拟供应商为其客户。')]

def fuling():
    clients=[
      dict(id='F01',name='收贮加工合作社',role='向农户收购原料，完成初加工后向加工企业交付',opening_fen=money(60),
           need='采购付款集中在年初，销售回款安排在下半年；先核实订单与存货，再讨论周转期限。',
           events=[event('F01-01','2027-01-20',-15,'盐料、包装及采购准备支出','模拟采购支出表'),
             event('F01-02','2027-02-05',-120,'分户原料采购款汇总','模拟分户采购清单'),
             event('F01-03','2027-02-20',-15,'加工、保管及运输支出汇总','模拟加工支出预算'),
             event('F01-04','2027-08-15',120,'首批交付回款','模拟半成品销售合同；交付验收待发生'),
             event('F01-05','2027-09-15',60,'剩余交付回款','模拟剩余批次回款安排')],
           materials=['采购合同与分户付款表','销售合同、交付和扣款条款','存货数量、质量及仓储记录','可用资金与现有借款清单'],
           missing='缺独立存货核验及交易对手确认，不能把拟销售额当作确定还款来源。',
           action='完成跨采购季周转需求核查',hours=8,hours_detail='材料核对2h＋现场/远程存货核验3h＋资金测算2h＋复核交接1h',
           outcome='一份有条件的周转需求与期限清单，供后续授信调查使用',
           stop='销售订单无法核实、存货权属不清或同一批货重复融资时，暂停进入融资方案。'),
      dict(id='F02',name='榨菜加工企业',role='采购原料并加工销售，部分渠道先收货款',opening_fen=money(220),
           need='本轮资料未显示现金短缺；关注采购批次付款与银行流水的对账差异。',
           events=[event('F02-01','2027-01-20',70,'经销预收款','模拟经销订单收款计划'),
             event('F02-02','2027-02-05',-180,'原料采购批次付款','模拟采购结算清单'),
             event('F02-03','2027-02-20',-40,'人工、加工与运营付款','模拟运营付款预算'),
             event('F02-04','2027-03-15',60,'销售回款','模拟渠道收款安排'),
             event('F02-05','2027-07-15',-30,'后续保管及经营付款','模拟后续经营预算')],
           materials=['已有结算产品清单','采购批次与流水样本','差错类型与人工处理记录','财务负责人对现有流程的确认'],
           missing='没有确认新增对账痛点，暂不能证明再做一个系统有价值。',
           action='核对现有结算覆盖与对账差异',hours=6,hours_detail='流程访谈2h＋样本勾稽2h＋差异分析1h＋建议确认1h',
           outcome='保留现有服务或提出一项可验证的对账改进',
           stop='现有系统已经覆盖需求、无可重复差错或客户不愿配合时，不启动改造。'),
      dict(id='F03',name='食品经销商',role='预付备货，随后通过下游渠道销售回款',opening_fen=money(32),
           need='备货付款更早到期；先看能否缩减首批备货，再判断周转需求。',
           events=[event('F03-01','2027-01-12',-60,'首批预付备货款','模拟采购订单'),
             event('F03-02','2027-01-25',-8,'仓配及运营付款','模拟仓配预算'),
             event('F03-03','2027-02-10',42,'首批渠道回款','模拟销售与回款计划'),
             event('F03-04','2027-03-10',30,'后续渠道回款','模拟后续销售与回款计划')],
           materials=['经销资格和采购订单','库存库龄及动销记录','下游销售回款明细','已有借款及担保情况'],
           missing='销售计划尚非已实现现金；先检验库存是否积压。',
           action='完成备货与短期周转核查',hours=6,hours_detail='订单库存核对2h＋回款核对2h＋方案比较1h＋复核1h',
           outcome='维持备货、缩小首批采购或进入融资调查的条件化建议',
           stop='动销不足、回款无法核实或新增资金仅用于掩盖逾期债务时，暂停新增融资建议。')]
    for c in clients:
        c['layer']='ASSUMPTION'; c['result']=curve(c['opening_fen'],c['events'],'2027-01-05','2027-09-30')
    stress=deepcopy(clients[0]['events'])
    for e in stress:
        if e['amount_fen']>0:e['date']=(date.fromisoformat(e['date'])+timedelta(days=14)).isoformat()
    # extend horizon so the delayed last payment is not silently dropped
    stress_result=curve(clients[0]['opening_fen'],stress,'2027-01-05','2027-10-31')
    return dict(clients=clients,capacity_hours=18,total_demand_hours=20,
                plan=dict(selected=['F03','F01'],used_hours=14,reserve_hours=4,deferred=['F02']),
                stress=stress_result,
                rule='先核实真实性，再按付款紧迫性和明确服务需求安排；不声称银行利润最优。',
                scenarios=[
                  dict(id='base',label='本周18小时',decision='先完成经销商6小时与合作社8小时核查，留4小时补件；加工企业6小时诊断排到下一批。',reason='1月12日备货付款更近；合作社占用期更长，需提前调查；加工企业暂无资金缺口且新需求未证实。'),
                  dict(id='tight',label='仅剩10小时',decision='完成经销商6小时核查；合作社先做2小时订单预检，保留2小时异常处理，其余调查排入下周。',reason='不把未完成的8小时调查包装成完成；若经销商订单无法核实，应暂停并把时间移给合作社。'),
                  dict(id='missing',label='经销订单存疑',decision='暂停经销商融资建议，先投入2小时核验；完成合作社8小时核查，余下8小时用于补件和加工企业需求确认。',reason='紧迫性不能越过真实性门槛；腾出的工时不等于自动推荐贷款。'),
                  dict(id='settlement',label='加工企业出现对账差错',decision='重新安排工时：先确认差错是否影响到期付款；若影响，优先投入2小时定位，合作社非紧急环节顺延。',reason='本周排序会随新事实改变。缺口金额不是唯一依据，运营付款风险也可能更紧迫。')])

def supplier():
    expenses=[event('A01','2027-01-15',-55,'材料采购付款','模拟材料采购合同'),
              event('A02','2027-02-10',-18,'人工与外协付款','模拟工资及外协付款表'),
              event('A03','2027-03-10',-12,'能源、运输等付款','模拟生产运营预算'),
              event('A04','2027-04-10',-6,'税费及其他到期付款','模拟企业现金支出计划；并非本订单税额推算')]
    due='2027-04-19';maturity='2027-07-19';discount_day='2027-04-20'
    days=(date.fromisoformat(maturity)-date.fromisoformat(discount_day)).days
    fee=int((Decimal(money(96))*Decimal('0.028')*days/365).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    scenarios=[
      dict(id='cash',label='现金按期到账',cash_date=due,fee_fen=0,
           events=expenses+[event('A05',due,96,'剩余货款现金到账','模拟合同付款安排')],
           recommendation='核实4月19日收款依据，同时在1月15日前解决采购付款缺口；仅等合同到期并不能保障生产。'),
      dict(id='bill',label='收到三个月银行承兑汇票',cash_date=maturity,fee_fen=0,
           events=expenses+[event('A05',maturity,96,'票据到期收款','模拟到期付款；仍存在不能按期兑付的可能')],
           recommendation='4月19日收到票据时，可用现金仍未增加。先核实票据、承兑人及可转让性，再比较持有到期与贴现。'),
      dict(id='discount',label='票据次日贴现成功',cash_date=discount_day,fee_fen=fee,
           events=expenses+[dict(event('A05',discount_day,96,'贴现净款到账','条件情景：票据可贴现、报价被接受且银行已办理'),amount_fen=money(96)-fee)],
           recommendation='在贴现成功的条件下缩短占用期，但不降低贴现前已形成的峰值缺口。不得把报价、申请或获批直接记为现金。'),
      dict(id='late',label='现金预计晚14天',cash_date='2027-05-03',fee_fen=0,
           events=expenses+[event('A05','2027-05-03',96,'情景预计收款','假设推迟14天；不构成延期合法性判断')],
           recommendation='同样56万元的峰值缺口持续更久；应重新确认过桥资金期限与到期付款，而不是只看授信额度是否够。')]
    for s in scenarios:s['result']=curve(money(35),s['events'],'2027-01-01','2027-07-31')
    return dict(company='汽车零部件供应商原型',layer='ASSUMPTION',opening_fen=money(35),
      contract_total_fen=money(120),advance_received_fen=money(24),remaining_fen=money(96),
      contract=dict(buyer='符合相关通知主体范围的整车企业原型',delivery='2027-03-19',acceptance='2027-03-20',invoice='2027-03-21',term='验收合格后30个自然日',payment_date=due,bill_maturity=maturity,discount_date=discount_day,discount_rate='2.8%',discount_days=days),
      cash_rule='期初35万元已含此前收到的24万元预付款，不能再次加总；所有情景均不包含未落实融资。',
      discount_rule='以票面96万元、年化2.8%、实际90天/365计息并四舍五入至分；不含另行收费，非银行报价。',
      scenarios=scenarios)

def build():
    data=dict(version='research-20261016',as_of='2026-10-16',scenario_period='2027年，前瞻模拟，非实际发生',
              disclosure='独立个人研究。公开资料用于解释产业机制；企业、合同、工时与收付数字均为构造案例，无银行合作、客户访谈或真实经营成果。',
              methodology='金额以分计算；按自然日日终累计；负值表示假定未补足资金时的测算缺口，不表示账户允许透支；未列现金流必须补齐后才可用于实际判断。',
              sources=SOURCES,fuling=fuling(),supplier=supplier())
    (ROOT/'dist'/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    return data
if __name__=='__main__':
    d=build()
    print(json.dumps({'fuling':{c['id']:{k:v for k,v in c['result'].items() if k!='daily'} for c in d['fuling']['clients']},'supplier':{s['id']:{k:v for k,v in s['result'].items() if k!='daily'} for s in d['supplier']['scenarios']},'discount_fee_fen':d['supplier']['scenarios'][2]['fee_fen']},ensure_ascii=False,indent=2))
