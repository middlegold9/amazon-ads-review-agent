from ads_agent.approve import notify, push_feishu, writes_allowed
from ads_agent.config import Settings


def test_writes_disabled_by_default():
    assert writes_allowed(Settings(approve_writes=False)) is False
    assert writes_allowed(Settings(approve_writes=True)) is True


class _FakeClient:
    def post(self, url, json):
        class R:
            status_code = 200

        return R()


def test_push_feishu_with_fake_client():
    assert push_feishu("https://hook", "hi", client=_FakeClient()) is True


def test_notify_uses_push_fn():
    called = {}

    def fn(report):
        called["r"] = report

    r = notify({"summary": "x"}, Settings(), push_fn=fn)
    assert r is True
    assert "r" in called
