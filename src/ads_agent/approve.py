"""审批网关 + 飞书/企微推送（US2/US4/FR7/FR8）。"""

from __future__ import annotations

from typing import Callable, Optional

import httpx

from .config import Settings


def writes_allowed(settings: Settings) -> bool:
    return bool(settings.approve_writes)


def push_feishu(webhook: str, text: str, client: Optional[httpx.Client] = None) -> bool:
    """向飞书自定义机器人 Webhook 推送文本消息。"""
    c = client or httpx.Client(timeout=15)
    resp = c.post(webhook, json={"msg_type": "text", "content": {"text": text}})
    return resp.status_code == 200


def notify(report: dict, settings: Settings,
           push_fn: Optional[Callable[[dict], None]] = None) -> Optional[bool]:
    """有 push_fn 用注入函数；否则按配置推飞书。"""
    if push_fn is not None:
        push_fn(report)
        return True
    if settings.feishu_webhook:
        return push_feishu(settings.feishu_webhook, report.get("summary", ""))
    return None
