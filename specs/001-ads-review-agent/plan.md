# Plan: Amazon 广告复盘 Agent

> 技术实现计划（Spec-Kit plan + Superpowers writing-plans 风格）。

## 技术栈
- Python 3.11+；编排 LangGraph（或简单 DAG）；LLM 用于叙事/nuanced 建议；规则引擎做确定性判断。
- 数据：经 `sp-api-mcp-server` 的 `ads_*`；存储 DuckDB（本地优先，零运维）。
- 调度：cron / 云函数；通知：飞书/企微 Webhook。
- 前端（可选）：Streamlit/Gradio 复盘看板。
- 测试：pytest；mock MCP 与 LLM。

## 目录结构
```
amazon-ads-review-agent/
├── pyproject.toml
├── .env.example
├── category_thresholds.yaml
├── src/ads_agent/
│   ├── __init__.py
│   ├── config.py            # 环境变量 + 阈值加载
│   ├── orchestrator.py      # LangGraph/DAG：采集→计算→诊断→建议→审批→执行→报告
│   ├── collect.py           # 调 MCP ads_* 拉报表/快照
│   ├── metrics.py           # ACOS/ROAS/TACOS/CTR/CVR/CPA/IS
│   ├── diagnose.py          # 规则引擎 + LLM 叙事
│   ├── suggest.py           # 建议生成 + 否定词挖掘
│   ├── approve.py           # 审批网关 + 飞书推送
│   ├── execute.py           # 经 MCP 写接口（护栏）
│   ├── report.py            # NL 报告 + 图表
│   ├── backtest.py          # 历史回测
│   └── strategies.py        # 规则库（版本化）
└── tests/
    ├── conftest.py
    ├── test_metrics.py
    ├── test_diagnose.py
    ├── test_suggest.py
    └── test_backtest.py
```

## 数据模型（data-model.md 摘要）
- `Snapshot{campaign_id, ad_group_id, keyword_id, impressions, clicks, spend, orders, sales, date}`。
- `Metric{ACOS, ROAS, TACOS, CTR, CVR, CPA, IS, IS_lost_budget, IS_lost_rank}`。
- `Diagnosis{rule, entity, severity, narrative, impact}`。
- `Suggestion{entity, action, old, new, rationale, expected_impact, confidence}`。
- `Effect{ts, suggestion_id, executed, acos_before, acos_after}`。

## 契约（contracts）
- 输入：MCP `ads_*` 工具（见 sp-api-mcp-server 契约）。
- 建议结构：`Suggestion`（上）。
- 审批协议：未授权执行返回 `{blocked:true}`；授权执行经 `execute.py` 调 MCP 写接口。
- 推送：飞书/企微 Webhook JSON。

## 研究（research.md 摘要）
- Ads API 报表异步 + gzip：创建→轮询 `status`→下载 `location`。
- 指标定义：ACOS=spend/sales；TACOS=广告销售/总销售；IS lost 来自 `impressionShares`。
- 否定词挖掘：searchterms 报表筛花费≥X 且 0 单且无关（余弦/包含匹配品牌词排除）。
- 回测：历史快照重放建议，对比实际 ACOS/ROAS。
- 归因不确定性：标注季节/库存影响。

## 关键风险与缓解
- 报表异步+gzip → 健壮轮询去重。
- 自动执行烧钱 → 护栏 + 默认关闭 + 审计。
- 归因复杂 → 诊断标注不确定性。

## 快速开始（quickstart.md 摘要）
1. `cp .env.example .env`，填 `MCP_BASE_URL`、`LLM_*`、`TARGET_ACOS`、`FEISHU_WEBHOOK`。
2. `pip install -e .`。
3. `python -m ads_agent.run --date 2026-07-04` 跑一次复盘。
4. 看 `reports/` 输出与飞书推送。

## 实现顺序（依赖）
1. 骨架 + config + metrics（US1/US2 基础）
2. collect（接 MCP） → diagnose（规则+LLM）
3. suggest（含否定词） → approve（网关+推送）
4. report（NL+图表） → backtest（回测）
5. strategies（规则库） → 多账户/阈值
6. 测试 + 手动验收
