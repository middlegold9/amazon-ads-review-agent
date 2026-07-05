# Tasks: Amazon 广告复盘 Agent

> Spec-Kit tasks（按用户故事；TDD：先测试后实现；`[P]` 可并行；精确路径 + 验证）。

## T1 — 骨架与指标计算（US1/US2 基础）
- [ ] `pyproject.toml`：声明 `mcp`(client)、`langgraph`、`pydantic`、`pandas`、`pydantic-settings`、`pytest`、飞书 SDK。
- [ ] `src/ads_agent/config.py`：读 `.env` + `category_thresholds.yaml`。
- [ ] `src/ads_agent/metrics.py`：`compute_metrics(snapshot)` → `Metric`（ACOS/ROAS/TACOS/CTR/CVR/CPA/IS）。
- [ ] `tests/test_metrics.py`：断言 ACOS=spend/sales 等公式正确。 **← TDD**
- **验证**：`pytest tests/test_metrics.py` 绿。

## T2 — 数据采集（依赖 sp-api-mcp-server）`[P]`
- [ ] `src/ads_agent/collect.py`：经 MCP `ads_profiles_list` → 遍历 → `ads_performance_report` + `ads_searchterms_report` + 快照，存 DuckDB。
- [ ] `tests/test_collect.py`：mock MCP 客户端，断言拉取+存储。 **← TDD**
- **验证**：本地 DuckDB 有快照表。

## T3 — 诊断引擎（US1/FR3/FR4）`[P]`
- [ ] `src/ads_agent/diagnose.py`：规则（ACOS>目标、花费无单、CTR<基准、预算早耗尽、排名跌、新竞品）+ LLM 叙事。
- [ ] `src/ads_agent/strategies.py`：规则库（版本化，可品类定制）。
- [ ] `tests/test_diagnose.py`：构造已知异常数据集，断言被识别 + 叙事生成。 **← TDD**
- **验证**：测试绿；异常召回达标。

## T4 — 建议生成 + 否定词挖掘（US2/US3/FR5/FR6）
- [ ] `src/ads_agent/suggest.py`：产出 `Suggestion`；否定词挖掘（searchterms 筛花费≥X 且 0 单且无关，排除品牌词）。
- [ ] `tests/test_suggest.py`：断言建议结构 + 否定词不误伤品牌词。 **← TDD**
- **验证**：测试绿；否定词列表准确。

## T5 — 审批网关 + 推送（US2/US4/FR7/FR8）
- [ ] `src/ads_agent/approve.py`：`require_approval()`；默认仅建议返回 `{blocked:true}`；飞书/企微 Webhook 推送日报 + 预警。
- [ ] `tests/test_approve.py`：断言未授权写被 block；推送 payload 正确。 **← TDD**
- [ ] `src/ads_agent/execute.py`：授权后经 MCP 写接口（预算/出价护栏）。
- **验证**：未开启自动执行仅建议；飞书收到推送。

## T6 — 复盘报告（US1/FR8）
- [ ] `src/ads_agent/report.py`：NL 摘要 + Top 5 异常/机会 + 图表（matplotlib）；写入 `reports/`。
- [ ] `tests/test_report.py`：断言报告含诊断与建议。 **← TDD**
- **验证**：`reports/` 生成日报。

## T7 — 回测框架（US5/FR9）
- [ ] `src/ads_agent/backtest.py`：历史快照重放建议，对比实际 ACOS/ROAS，出吻合率。
- [ ] `tests/test_backtest.py`：小数据集断言回测产出指标。 **← TDD**
- **验证**：回测产出吻合率。

## T8 — 编排与调度（串联 US1–US5）
- [ ] `src/ads_agent/orchestrator.py`：LangGraph/DAG 串联 T2→T1→T3→T4→T5→T6（T7 离线）。
- [ ] `python -m ads_agent.run` 入口 + cron 示例。
- **验证**：跑一次端到端复盘，飞书收到日报。

## T9 — 多账户与品类阈值（US6/FR10）
- [ ] `category_thresholds.yaml` 支持 3C/服饰；`config.py` 按品类加载。
- [ ] 多 profile 遍历已在 T2；补阈值路由。
- **验证**：不同品类用不同阈值诊断。

## 并行与检查点
- T2/T3 可并行；T4/T5/T6 依赖 T3；T7 离线可并行 T8。
- **人工检查点**（executing-plans）：T3 诊断规则库完成后暂停，人工用真实店铺数据抽检诊断准确性，再继续 T4+。
- 每任务 RED→GREEN→REFACTOR；提交前 `pytest` 全绿（verification-before-completion）。
