from ads_agent.metrics import compute_metrics
from ads_agent.models import Snapshot


def test_metrics_formulas():
    s = Snapshot(campaign_id="c1", impressions=1000, clicks=20, spend=10, orders=2, sales=40)
    m = compute_metrics(s)
    assert abs(m.acos - 0.25) < 1e-9
    assert abs(m.roas - 4.0) < 1e-9
    assert abs(m.ctr - 0.02) < 1e-9
    assert abs(m.cvr - 0.1) < 1e-9
    assert abs(m.cpa - 5.0) < 1e-9


def test_metrics_zero_sales_no_acos():
    s = Snapshot(campaign_id="c1", spend=5, sales=0, impressions=100, clicks=3)
    m = compute_metrics(s)
    assert m.acos is None
    assert m.ctr == 0.03
