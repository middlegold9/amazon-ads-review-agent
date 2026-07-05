"""数据采集（依赖 sp-api-mcp-server）：经 MCP ads_* 拉报表并解析（US3/FR7）。"""

from __future__ import annotations

import csv
import io
from typing import Callable, List, Optional

import httpx

from .models import SearchTerm, Snapshot


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def parse_performance_csv(text: str) -> List[Snapshot]:
    reader = csv.DictReader(io.StringIO(text or ""))
    out: List[Snapshot] = []
    for row in reader:
        out.append(Snapshot(
            campaign_id=row.get("campaignId") or row.get("campaign_id") or "",
            ad_group_id=row.get("adGroupId") or row.get("ad_group_id") or "",
            keyword_id=row.get("keywordId") or row.get("keyword_id") or "",
            date=row.get("date") or "",
            impressions=_f(row.get("impressions")),
            clicks=_f(row.get("clicks")),
            spend=_f(row.get("cost") or row.get("spend")),
            orders=_f(row.get("attributedConversions1d") or row.get("orders")),
            sales=_f(row.get("attributedSales1d") or row.get("sales")),
        ))
    return out


def parse_searchterms_csv(text: str) -> List[SearchTerm]:
    reader = csv.DictReader(io.StringIO(text or ""))
    out: List[SearchTerm] = []
    for row in reader:
        out.append(SearchTerm(
            keyword_id=row.get("keywordId") or "",
            query=row.get("query") or "",
            impressions=_f(row.get("impressions")),
            clicks=_f(row.get("clicks")),
            spend=_f(row.get("cost") or row.get("spend")),
            orders=_f(row.get("attributedConversions1d") or row.get("orders")),
            sales=_f(row.get("attributedSales1d") or row.get("sales")),
        ))
    return out


class MCPClient:
    """对 sp-api-mcp-server 的 tools/call 封装；返回 Envelope.data。"""

    def __init__(self, base_url: str = "", token: str = "", client: Optional[httpx.Client] = None):
        self.base_url = base_url
        self.token = token
        self._client = client or httpx.Client(timeout=30)

    def call(self, name: str, args: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = self._client.post(
            f"{self.base_url}/tools/call",
            headers=headers,
            json={"name": name, "arguments": args},
        )
        resp.raise_for_status()
        body = resp.json()
        return body.get("data", body)


def collect(
    date: str,
    profiles: List[str],
    client: MCPClient,
    record_types: tuple = ("campaigns", "adgroups", "keywords"),
    searchterms: bool = True,
) -> dict:
    """采集性能报表 + 搜索词报表，返回 {snapshots, searchterms}。"""
    snapshots: List[Snapshot] = []
    sts: List[SearchTerm] = []
    for pid in profiles:
        for rt in record_types:
            data = client.call(
                "ads_performance_report",
                {"profile_id": pid, "record_type": rt, "report_date": date},
            )
            snapshots += parse_performance_csv(data.get("content", ""))
        if searchterms:
            data = client.call(
                "ads_searchterms_report",
                {"profile_id": pid, "report_date": date},
            )
            sts += parse_searchterms_csv(data.get("content", ""))
    return {"snapshots": snapshots, "searchterms": sts}
