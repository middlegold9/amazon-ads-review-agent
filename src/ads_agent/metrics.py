"""指标计算（US1/US2）：ACOS / ROAS / TACOS / CTR / CVR / CPA / IS。"""

from __future__ import annotations

from .models import Metric, Snapshot


def compute_metrics(s: Snapshot) -> Metric:
    acos = s.spend / s.sales if s.sales > 0 else None
    roas = s.sales / s.spend if s.spend > 0 else None
    tacos = (s.sales / s.total_sales) if (s.total_sales and s.total_sales > 0) else None
    ctr = s.clicks / s.impressions if s.impressions > 0 else None
    cvr = s.orders / s.clicks if s.clicks > 0 else None
    cpa = s.spend / s.orders if s.orders > 0 else None
    return Metric(
        acos=acos,
        roas=roas,
        tacos=tacos,
        ctr=ctr,
        cvr=cvr,
        cpa=cpa,
        is_share=s.impression_share,
        is_lost_budget=s.is_lost_budget,
        is_lost_rank=s.is_lost_rank,
    )
