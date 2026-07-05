from ads_agent.collect import MCPClient
from ads_agent.config import Settings
from ads_agent.orchestrator import run


class FakeClient(MCPClient):
    def call(self, name, args):
        if name == "ads_profiles_list":
            return {"profiles": [{"profileId": "p1"}]}
        if name == "ads_performance_report":
            return {
                "content": (
                    "campaignId,impressions,clicks,cost,attributedConversions1d,attributedSales1d\n"
                    "c1,1000,20,10,2,40\n"
                    "c2,500,0,8,0,0\n"
                )
            }
        if name == "ads_searchterms_report":
            return {
                "content": (
                    "keywordId,query,impressions,clicks,cost,attributedConversions1d,attributedSales1d\n"
                    "k1,blue shoes,100,5,10,0,0\n"
                )
            }
        return {"content": ""}


def test_run_full_pipeline_only_suggest():
    settings = Settings(approve_writes=False, category="default")
    report = run("2024-01-01", FakeClient(), settings, brand_keywords=["brand"])
    assert report["overall_acos"] is not None
    rules = {d["rule"] for d in report["diagnoses"]}
    assert "spend_no_order" in rules
    assert report["auto_executed"] is False
    # 否定词应包含 blue shoes，不应包含品牌
    nk = {s["entity"] for s in report["suggestions"] if s["action"] == "add_negative_kw"}
    assert "blue shoes" in nk


def test_run_with_auto_execute():
    settings = Settings(approve_writes=True, category="default")
    report = run("2024-01-01", FakeClient(), settings, brand_keywords=["brand"])
    assert report["auto_executed"] is True
