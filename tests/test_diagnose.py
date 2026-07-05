from ads_agent.diagnose import diagnose
from ads_agent.metrics import compute_metrics
from ads_agent.models import Snapshot
from ads_agent.strategies import get_thresholds


def test_acos_above_target():
    s = Snapshot(campaign_id="c1", spend=10, sales=20)  # ACOS 0.5 > 0.25
    d = diagnose(s, compute_metrics(s), get_thresholds("default"))
    assert any(x.rule == "acos_above_target" for x in d)


def test_spend_no_order():
    s = Snapshot(campaign_id="c1", spend=5, sales=0, orders=0)
    d = diagnose(s, compute_metrics(s), get_thresholds())
    assert any(x.rule == "spend_no_order" for x in d)


def test_low_ctr_and_cvr():
    s = Snapshot(campaign_id="c1", impressions=10000, clicks=5, spend=2, orders=0, sales=0)
    d = diagnose(s, compute_metrics(s), get_thresholds())
    rules = {x.rule for x in d}
    assert "low_ctr" in rules
    assert "low_cvr" in rules


def test_clean_campaign_no_diagnosis():
    s = Snapshot(campaign_id="c1", impressions=1000, clicks=50, spend=10, orders=5, sales=50)
    d = diagnose(s, compute_metrics(s), get_thresholds())
    assert d == []
