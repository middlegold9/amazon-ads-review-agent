"""建议生成 + 否定词挖掘（US2/US3/FR5/FR6）。"""

from __future__ import annotations

from typing import List, Optional

from .models import Diagnosis, SearchTerm, Snapshot, Suggestion


def _is_brand(query: str, brand_keywords: Optional[List[str]]) -> bool:
    if not brand_keywords:
        return False
    q = (query or "").lower()
    return any(b.lower() in q for b in brand_keywords)


def suggest(
    snapshots: List[Snapshot],
    diagnoses: List[Diagnosis],
    thresholds: dict,
    searchterms: Optional[List[SearchTerm]] = None,
    brand_keywords: Optional[List[str]] = None,
) -> List[Suggestion]:
    out: List[Suggestion] = []
    seen = set()

    for d in diagnoses:
        if d.rule == "acos_above_target":
            reduce = float(thresholds.get("bid_reduce_pct", 0.15))
            out.append(Suggestion(
                entity=d.entity, action="reduce_bid",
                old=1.0, new=round(1.0 - reduce, 3),
                rationale="ACOS 超标，下调出价以控本",
                expected_impact="ACOS 下降、流量略减", confidence=0.7,
            ))
        elif d.rule == "spend_no_order":
            out.append(Suggestion(
                entity=d.entity, action="pause_or_review",
                rationale="烧钱无转化，建议暂停或复查定向/匹配方式",
                expected_impact="停止无效花费", confidence=0.8,
            ))
        elif d.rule in ("low_ctr", "low_cvr"):
            out.append(Suggestion(
                entity=d.entity, action="optimize_creative",
                rationale="点击率/转化率偏低，建议优化创意或落地页",
                expected_impact="提升转化效率", confidence=0.5,
            ))

    # 否定词挖掘
    if searchterms:
        for st in searchterms:
            if (st.spend >= thresholds["neg_kw_spend"]
                    and st.orders <= thresholds["neg_kw_orders"]
                    and not _is_brand(st.query, brand_keywords)):
                key = f"nk::{st.query}"
                if key in seen:
                    continue
                seen.add(key)
                out.append(Suggestion(
                    entity=st.query, action="add_negative_kw",
                    rationale=f"搜索词 '{st.query}' 花费 ${st.spend:.2f} 但 0 单",
                    expected_impact="减少无效花费", confidence=0.8,
                ))

    for i, s in enumerate(out, 1):
        s.suggestion_id = f"S{i}"
    return out
