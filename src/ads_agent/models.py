"""广告复盘数据模型。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Snapshot(BaseModel):
    profile_id: str = ""
    campaign_id: str
    ad_group_id: str = ""
    keyword_id: str = ""
    date: str = ""
    impressions: float = 0.0
    clicks: float = 0.0
    spend: float = 0.0
    orders: float = 0.0
    sales: float = 0.0
    total_sales: Optional[float] = None
    impression_share: Optional[float] = None
    is_lost_budget: Optional[float] = None
    is_lost_rank: Optional[float] = None


class Metric(BaseModel):
    acos: Optional[float] = None
    roas: Optional[float] = None
    tacos: Optional[float] = None
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    cpa: Optional[float] = None
    is_share: Optional[float] = None
    is_lost_budget: Optional[float] = None
    is_lost_rank: Optional[float] = None


class Diagnosis(BaseModel):
    rule: str
    entity: str
    severity: str  # high | medium | low
    narrative: str
    impact: Optional[float] = None


class Suggestion(BaseModel):
    suggestion_id: str = ""
    entity: str
    action: str  # reduce_bid | pause_or_review | optimize_creative | add_negative_kw | increase_budget
    old: Optional[float] = None
    new: Optional[float] = None
    rationale: str = ""
    expected_impact: str = ""
    confidence: float = 0.5


class Effect(BaseModel):
    ts: float
    suggestion_id: str
    executed: bool
    acos_before: Optional[float] = None
    acos_after: Optional[float] = None


class SearchTerm(BaseModel):
    keyword_id: str = ""
    query: str
    impressions: float = 0.0
    clicks: float = 0.0
    spend: float = 0.0
    orders: float = 0.0
    sales: float = 0.0
