import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'research'))
from models import supplier_case,deposit_case

def test_supplier_independent_reference():
    x=supplier_case()
    # 8+12-30-12-4=-26万元; shortage day7 through44 =38 days.
    assert x['peak_gap_fen']==26000000 and x['negative_days']==38
    assert x['closing_fen']==22000000
    y=supplier_case('.4',14,'.02','1000')
    assert y['peak_gap_fen']==14100000 and y['negative_days']==39
    assert y['discount_cost_fen']==720000 and y['closing_fen']==21180000

def test_deposit_independent_reference():
    x=deposit_case() # V2: 1000万×(80%×2%-1.5%)-2万=-1万；未承诺资产，不计替代资金成本
    assert x['contribution_fen']==-1000000
    assert float(x['break_even_rate'])==.014
    assert deposit_case(rate='.014')['contribution_fen']==0

def test_monotonicity():
    assert supplier_case(delay_days=14)['negative_days']>supplier_case()['negative_days']
    assert deposit_case(effective_funding_factor='.9')['contribution_fen']>deposit_case()['contribution_fen']
    assert deposit_case(rate='.02')['contribution_fen']<deposit_case()['contribution_fen']

def test_resource_allocation_matches_exhaustive_reference():
    from models import allocate_actions
    import itertools
    actions=[{'id':str(i),'hours':h,'benefit_fen':v} for i,(h,v) in enumerate([(2,5),(3,7),(4,11),(1,-2),(5,12)])]
    best=max(sum(a['benefit_fen'] for a,t in zip(actions,bits) if t) for bits in itertools.product([0,1],repeat=5) if sum(a['hours'] for a,t in zip(actions,bits) if t)<=8)
    result=allocate_actions(actions,8)
    assert result['benefit_fen']==best and result['hours']<=8
