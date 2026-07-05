"""规则库（版本化，可品类定制）。阈值可被 category_thresholds.yaml 覆盖。"""

from __future__ import annotations

from typing import Dict

# 默认阈值（也可由 category_thresholds.yaml 提供）
DEFAULT_THRESHOLDS: Dict[str, float] = {
    "target_acos": 0.25,
    "min_ctr": 0.003,
    "min_cvr": 0.05,
    "neg_kw_spend": 5.0,   # 否定词挖掘：单搜索词花费阈值
    "neg_kw_orders": 0,    # 且订单数 <= 此值
    "bid_reduce_pct": 0.15,
}

# 品类定制
CATEGORY_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "electronics": {"target_acos": 0.18, "min_ctr": 0.0025, "min_cvr": 0.04,
                    "neg_kw_spend": 8.0, "neg_kw_orders": 0, "bid_reduce_pct": 0.12},
    "apparel": {"target_acos": 0.30, "min_ctr": 0.004, "min_cvr": 0.06,
                "neg_kw_spend": 4.0, "neg_kw_orders": 0, "bid_reduce_pct": 0.18},
}

RULESET_VERSION = "1.0.0"


def get_thresholds(category: str = "default") -> Dict[str, float]:
    base = dict(DEFAULT_THRESHOLDS)
    base.update(CATEGORY_THRESHOLDS.get(category, {}))
    return base
