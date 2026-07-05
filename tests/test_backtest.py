from ads_agent.backtest import backtest
from ads_agent.models import Suggestion


def test_match_rate():
    items = [
        (Suggestion(entity="c1", action="reduce_bid", suggestion_id="S1"), 0.5, 0.4),
        (Suggestion(entity="c2", action="reduce_bid", suggestion_id="S2"), 0.5, 0.6),
    ]
    r = backtest(items)
    assert r["total"] == 2
    assert r["matched"] == 1
    assert abs(r["match_rate"] - 0.5) < 1e-9


def test_all_matched():
    items = [(Suggestion(entity="c1", action="add_negative_kw", suggestion_id="S1"), 0.3, 0.2)]
    r = backtest(items)
    assert r["match_rate"] == 1.0
