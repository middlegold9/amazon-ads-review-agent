"""执行建议（经 MCP 写接口，受审批网关约束，带预算护栏）。"""

from __future__ import annotations

import time

from .approve import writes_allowed
from .config import Settings
from .models import Effect, Suggestion


def execute_suggestion(
    sugg: Suggestion,
    client,
    settings: Settings,
    acos_before: float = None,
) -> Effect:
    """默认仅建议（不执行）。开启 approve_writes 后落库到广告后台。"""
    if not writes_allowed(settings):
        return Effect(
            ts=time.time(),
            suggestion_id=sugg.suggestion_id,
            executed=False,
            acos_before=acos_before,
        )

    # 预算/出价护栏：下调出价不得低于原值 50%
    if sugg.action == "reduce_bid" and sugg.new is not None and sugg.old:
        if sugg.new < sugg.old * 0.5:
            sugg = sugg.model_copy(update={"new": round(sugg.old * 0.5, 3)})

    if sugg.action == "reduce_bid":
        client.call("ads_campaign_update", {
            "profile_id": sugg.entity, "campaign_id": sugg.entity,
            "patch": {"bid": sugg.new},
        })
    elif sugg.action == "add_negative_kw":
        client.call("ads_negative_keyword_create", {
            "profile_id": sugg.entity,
            "body": {"keywordText": sugg.entity, "matchType": "negativeExact"},
        })
    # pause_or_review / optimize_creative 为人工动作，不自动执行

    return Effect(
        ts=time.time(),
        suggestion_id=sugg.suggestion_id,
        executed=True,
        acos_before=acos_before,
    )
