import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "fuling", Path(__file__).parent / "examples/fuling.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_hand_calculated_reference():
    row = dict(
        sector="制造业",
        loan=100,
        deposit=80,
        loan_rate=0.05,
        deposit_rate=0.01,
        pd=0.02,
        lgd=0.5,
        fee=1,
        hours=12,
    )
    x = m.calculate([row], m.STRATEGIES[0], m.STRESSES[0], rm=3)
    # 5 interest - .8 deposit - .4 net FTP + 1 fee - 1 expected loss - 54 staff
    assert x["contribution"] == -50.2
    y = m.calculate([row], m.STRATEGIES[0], m.STRESSES[1], rm=3)
    assert y["contribution"] == -50.7
    assert m.calculate([row], m.STRATEGIES[0], m.STRESSES[3], rm=3)["el"] == 2


def test_deterministic_capacity_and_monotone_stress():
    assert m.customers() == m.customers()
    for s in m.STRATEGIES:
        base = m.calculate(m.customers(), s, m.STRESSES[0])
        stress = m.calculate(m.customers(), s, m.STRESSES[-1])
        assert stress["contribution"] < base["contribution"]
    row = m.customers()[0]
    row["hours"] = 4000
    assert not m.calculate([row], m.STRATEGIES[0], m.STRESSES[0], rm=3)["feasible"]
