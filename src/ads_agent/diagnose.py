"""诊断引擎（US1/FR3/FR4）：规则 + 可选 LLM 叙事。"""

from __future__ import annotations

from typing import Callable, List, Optional

from .models import Diagnosis, Metric, Snapshot


def diagnose(
    snapshot: Snapshot,
    metric: Metric,
    thresholds: dict,
    llm_fn: Optional[Callable[[str], str]] = None,
) -> List[Diagnosis]:
    out: List[Diagnosis] = []
    target = thresholds["target_acos"]

    if metric.acos is not None and metric.acos > target:
        out.append(Diagnosis(
            rule="acos_above_target",
            entity=snapshot.campaign_id,
            severity="high",
            narrative=f"ACOS {metric.acos:.1%} 高于目标 {target:.1%}",
        ))
    if snapshot.spend > 0 and snapshot.orders == 0:
        out.append(Diagnosis(
            rule="spend_no_order",
            entity=snapshot.campaign_id,
            severity="high",
            narrative=f"花费 ${snapshot.spend:.2f} 但 0 转化",
            impact=snapshot.spend,
        ))
    if metric.ctr is not None and metric.ctr < thresholds["min_ctr"]:
        out.append(Diagnosis(
            rule="low_ctr",
            entity=snapshot.campaign_id,
            severity="medium",
            narrative=f"CTR {metric.ctr:.2%} 低于基准 {thresholds['min_ctr']:.2%}",
        ))
    if metric.cvr is not None and metric.cvr < thresholds["min_cvr"]:
        out.append(Diagnosis(
            rule="low_cvr",
            entity=snapshot.campaign_id,
            severity="medium",
            narrative=f"CVR {metric.cvr:.2%} 低于基准 {thresholds['min_cvr']:.2%}",
        ))

    if llm_fn is not None and out:
        for d in out:
            d.narrative = llm_fn(d.narrative)
    return out
