"""编排（DAG）：采集 → 计算 → 诊断 → 建议 → 审批/执行 → 报告/推送。"""

from __future__ import annotations

from typing import Callable, List, Optional

from .approve import notify, writes_allowed
from .collect import MCPClient, collect
from .config import Settings, get_settings
from .diagnose import diagnose
from .execute import execute_suggestion
from .metrics import compute_metrics
from .models import Effect, Snapshot
from .report import build_report
from .strategies import get_thresholds
from .suggest import suggest


def run(
    date: str,
    client: MCPClient,
    settings: Optional[Settings] = None,
    profiles: Optional[List[str]] = None,
    llm_fn: Optional[Callable[[str], str]] = None,
    push_fn: Optional[Callable[[dict], None]] = None,
    brand_keywords: Optional[List[str]] = None,
) -> dict:
    settings = settings or get_settings()
    if profiles is None:
        prof_data = client.call("ads_profiles_list", {})
        profiles = [p.get("profileId") for p in prof_data.get("profiles", prof_data if isinstance(prof_data, list) else [])]

    collected = collect(date, profiles, client)
    snapshots: List[Snapshot] = collected["snapshots"]
    searchterms = collected["searchterms"]

    metrics_map = {s.campaign_id: compute_metrics(s) for s in snapshots}
    thresholds = get_thresholds(settings.category)

    diagnoses = []
    for s in snapshots:
        diagnoses += diagnose(s, metrics_map[s.campaign_id], thresholds, llm_fn)

    suggestions = suggest(
        snapshots, diagnoses, thresholds,
        searchterms=searchterms, brand_keywords=brand_keywords,
    )

    effects: List[Effect] = []
    if writes_allowed(settings):
        for sugg in suggestions:
            effects.append(execute_suggestion(sugg, client, settings))

    report = build_report(date, snapshots, metrics_map, diagnoses, suggestions)
    report["effects"] = [e.model_dump() for e in effects]
    report["auto_executed"] = writes_allowed(settings)

    notify(report, settings, push_fn=push_fn)
    return report
