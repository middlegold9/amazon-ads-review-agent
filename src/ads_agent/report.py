"""复盘报告：NL 摘要 + Top 异常 + 可选图表（US1/FR8）。"""

from __future__ import annotations

from typing import Dict, List

from .models import Diagnosis, Metric, Snapshot, Suggestion

_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def build_report(
    date: str,
    snapshots: List[Snapshot],
    metrics_map: Dict[str, Metric],
    diagnoses: List[Diagnosis],
    suggestions: List[Suggestion],
) -> dict:
    total_spend = sum(s.spend for s in snapshots)
    total_sales = sum(s.sales for s in snapshots)
    total_orders = sum(s.orders for s in snapshots)
    overall_acos = (total_spend / total_sales) if total_sales > 0 else None

    summary = (
        f"广告复盘 {date}：覆盖 {len(snapshots)} 个实体，"
        f"总花费 ${total_spend:.2f}，总销售额 ${total_sales:.2f}，"
        f"总订单 {int(total_orders)}，整体 ACOS "
        f"{overall_acos:.1%}" if overall_acos is not None else "N/A"
    )

    top = sorted(diagnoses, key=lambda d: _SEVERITY_RANK.get(d.severity, 9))[:5]

    return {
        "date": date,
        "summary": summary,
        "overall_acos": overall_acos,
        "total_spend": total_spend,
        "total_sales": total_sales,
        "diagnoses": [d.model_dump() for d in diagnoses],
        "suggestions": [s.model_dump() for s in suggestions],
        "top_anomalies": [d.model_dump() for d in top],
    }


def render_chart(report: dict, out_path: str) -> Optional[str]:
    """可选：用 matplotlib 画整体 ACOS 与建议数（未装 matplotlib 时跳过）。"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:  # noqa: BLE001
        return None
    fig, ax = plt.subplots()
    ax.bar(["spend", "sales"], [report["total_spend"], report["total_sales"]])
    ax.set_title(f"Ad Review {report['date']}")
    fig.savefig(out_path)
    return out_path
