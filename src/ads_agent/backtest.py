"""回测框架（US5/FR9）：重放历史建议，对比实际 ACOS/ROAS，出吻合率。"""

from __future__ import annotations

from typing import List, Tuple

from .models import Suggestion


def backtest(items: List[Tuple[Suggestion, float, float]]) -> dict:
    """items: (建议, 执行前 ACOS, 执行后 ACOS)。返回吻合率。"""
    total = 0
    matched = 0
    for sugg, before, after in items:
        total += 1
        if before is None or after is None:
            continue
        direction_ok = True
        if sugg.action in ("reduce_bid", "add_negative_kw", "pause_or_review"):
            direction_ok = after <= before  # 预期 ACOS 不升
        elif sugg.action == "increase_budget":
            direction_ok = after >= before
        if direction_ok:
            matched += 1
    return {
        "total": total,
        "matched": matched,
        "match_rate": (matched / total) if total else 0.0,
    }
