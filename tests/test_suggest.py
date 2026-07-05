from ads_agent.models import Diagnosis, SearchTerm
from ads_agent.strategies import get_thresholds
from ads_agent.suggest import suggest


def test_reduce_bid_suggestion():
    diag = [Diagnosis(rule="acos_above_target", entity="c1", severity="high", narrative="x")]
    out = suggest([], diag, get_thresholds())
    assert any(s.action == "reduce_bid" for s in out)


def test_pause_for_spend_no_order():
    diag = [Diagnosis(rule="spend_no_order", entity="c1", severity="high", narrative="x")]
    out = suggest([], diag, get_thresholds())
    assert any(s.action == "pause_or_review" for s in out)


def test_negative_keyword_excludes_brand():
    diag = []
    sts = [
        SearchTerm(query="nike red shoes", spend=10, orders=0),
        SearchTerm(query="blue shoes", spend=10, orders=0),
    ]
    out = suggest([], diag, get_thresholds(), searchterms=sts, brand_keywords=["nike"])
    nk = {s.entity for s in out if s.action == "add_negative_kw"}
    assert "nike red shoes" not in nk
    assert "blue shoes" in nk


def test_negative_keyword_skips_converting_term():
    diag = []
    sts = [SearchTerm(query="good boots", spend=10, orders=3)]
    out = suggest([], diag, get_thresholds(), searchterms=sts)
    assert not any(s.action == "add_negative_kw" for s in out)
