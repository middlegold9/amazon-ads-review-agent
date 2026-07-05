# amazon-ads-review-agent

> **Amazon 广告复盘 Agent** —— 自动拉取广告报表、诊断异常、给调价与否定词建议，可验证可复盘。
> 运营的 hero 场景，outcome 最硬（ACOS↓、人效↑），最易量化验证、最易讲成面试故事。

> 状态：**已落地 + 17/17 单测通过**（Python，含完整 orchestrator 链路）。默认**仅建议**，人类审批后才可选执行。

---

## 1. 这个工具解决什么问题

PPC 运营每天：从广告后台拉报表 → 找异常（烧钱无转化、曝光跌、ACOS 超标）→ 调价 / 加否定词 / 调预算。一个运营管数十个活动，手工 1–2h/天，且高度依赖经验，易漏、易错、难复盘。

本 Agent 把「**采集 → 计算 → 诊断 → 建议 → 审批 → 执行 → 复盘 → 回测**」自动化：

- **省人效**：每天自动出诊断与建议，运营只做审批，处理时长可降 60%+。
- **可验证**：用历史快照回测，诊断建议与资深运营操作的吻合率可量化（目标 ≥ 85%）。
- **可复盘**：策略沉淀为版本化规则库，按品类（3C / 服饰）配置阈值，越用越准。
- **不烧钱**：写执行（调价 / 否定词）默认关闭，受审批网关 + 出价护栏（下调不低于原值 50%）双重保护。

---

## 2. 核心能力

| 能力 | 说明 |
|---|---|
| **指标计算** | ACOS、ROAS、TACOS、CTR、CVR、CPA、曝光份额（IS）等。 |
| **数据采集** | 经 `sp-api-mcp-server` 的 `ads_*` 工具拉表现 / 搜索词报表（异步 → 轮询 → gzip 下载），CSV 解析，本地快照便于回测。 |
| **诊断引擎** | 规则层：`acos_above_target`、`spend_no_order`、`low_ctr`、`low_cvr`；可选 LLM 层生成自然语言归因 + 影响估算。 |
| **建议生成** | 调价 / 暂停 / 优化创意 / 否定词挖掘。否定词从搜索词报表筛「有花费且 0 单且无关」候选（**自动排除品牌词**，防误伤）。 |
| **审批网关** | 默认 `writes_allowed=false` → 仅建议不执行；开启 `ADS_APPROVE_WRITES` 后才落库，且出价下调不低于原值 50%。 |
| **复盘报告** | 自然语言摘要 + Top 异常 / Top 机会 + 可选图表，推送到飞书 / 企微 Webhook。 |
| **回测验证** | 读历史快照重放建议，对比「若执行当时建议」vs 实际，出吻合率。 |
| **策略库** | 规则版本化 + `category_thresholds.yaml` 按品类配置阈值。 |

---

## 3. 端到端链路

```
[cron 每日 09:00 / 周]
  └─ ads_profiles_list → 各市场 profileId
       └─ 采集：ads_performance_report + ads_searchterms_report + 快照
            └─ 指标计算：ACOS / ROAS / TACOS / CTR / CVR ...
                 └─ 诊断引擎（规则 + 可选 LLM 叙事）
                      └─ 建议生成（调价 / 否定词 / 预算 / 暂停）
                           └─ 审批网关（飞书卡片 → 运营确认 / 修改 / 驳回）
                                └─ 执行（若批准，带出价护栏，经 sp-api-mcp 写接口）
                                     └─ 复盘报告（NL + 图表 + 推送）
                                          └─ 反馈闭环：建议→是否执行→后续效果
                                               └─ 策略库沉淀（高速公路）
```

---

## 4. 快速开始

```bash
cd amazon-ads-review-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
# 或装：pydantic pydantic-settings httpx pyyaml
cp .env.example .env   # 填 MCP_BASE_URL / ADS_APPROVE_WRITES / FEISHU_WEBHOOK / TARGET_ACOS
```

### 跑一次复盘（编排入口 `orchestrator.run`）

```python
from ads_agent.orchestrator import run
from ads_agent.collect import MCPClient

# 真实接入：把 base_url 指向 sp-api-mcp-server 的 SSE/HTTP 端点
client = MCPClient(base_url="http://localhost:8000", token="")

report = run(
    date="2026-07-04",
    client=client,
    brand_keywords=["yourbrand"],   # 用于否定词挖掘时排除品牌词
    # push_fn=my_feishu_pusher,     # 可选：注入推送函数
)
print(report["summary"])            # 自然语言复盘摘要
print(report["auto_executed"])      # False（默认仅建议）
```

> 单测里用 stub `MCPClient`（直接返回样例 CSV）即可离线跑通整条链路，无需真实亚马逊凭证。

---

## 5. 关键函数 / 模块用法

| 模块 | 用途 | 关键函数 |
|---|---|---|
| `metrics` | 指标计算 | `compute_metrics(snapshot) -> Metric` |
| `collect` | 经 MCP 拉报表 + CSV 解析 | `MCPClient(base_url, token).call(name, args)`；`collect(date, profiles, client)` |
| `diagnose` | 规则 + 可选 LLM 叙事 | `diagnose(snapshot, metric, thresholds, llm_fn)` |
| `strategies` | 版本化规则 + 品类阈值 | `get_thresholds(category)` |
| `suggest` | 建议 + 否定词挖掘 | `suggest(snapshots, diagnoses, thresholds, searchterms, brand_keywords)` |
| `approve` | 审批网关 + 飞书推送 | `writes_allowed(settings)`；`notify(report, settings, push_fn)` |
| `execute` | 经 MCP 写接口（带护栏） | `execute_suggestion(sugg, client, settings)` |
| `report` | NL 摘要 + 图表 | `build_report(date, snapshots, metrics_map, diagnoses, suggestions)` |
| `backtest` | 历史重放吻合率 | `backtest(snapshots, suggestions, actual)` |
| `orchestrator` | 串起以上 DAG | `run(date, client, settings, profiles, llm_fn, push_fn, brand_keywords)` |

### 5.1 建议结构（结构化）
```json
{
  "entity": "campaignId",
  "action": "reduce_bid | add_negative_kw | pause_or_review | optimize_creative",
  "old": 1.20, "new": 0.95,
  "rationale": "ACOS 高于目标且花费超中位",
  "expected_impact": "ACOS 预计下降 N%",
  "confidence": 0.8
}
```

### 5.2 否定词挖掘（自动排除品牌词）
```python
from ads_agent.suggest import suggest
suggestions = suggest(snaps, diags, thr, searchterms=sts, brand_keywords=["yourbrand"])
# 仅返回「有花费、0 单、且与品牌无关」的候选否定词，避免误伤自身品牌流量
```

### 5.3 回测
```python
from ads_agent.backtest import backtest
score = backtest(snapshots, suggestions, actual_effects)
# → 吻合率（建议与实际执行的重叠度），用于校验诊断准确率
```

---

## 6. 配置项（环境变量）

| 变量 | 说明 |
|---|---|
| `MCP_BASE_URL` / `MCP_TOKEN` | 指向 `sp-api-mcp-server` 端点（数据源 + 写执行） |
| `TARGET_ACOS` | 目标 ACOS 阈值（诊断触发线） |
| `ADS_APPROVE_WRITES` | `false`（默认，仅建议）/ `true`（允许自动执行） |
| `BUDGET_CHANGE_CAP` | 单次预算变更上限（护栏） |
| `FEISHU_WEBHOOK` | 飞书自定义机器人 Webhook，复盘报告推送 |
| `CATEGORY` | 品类（读 `category_thresholds.yaml` 的 3C / 服饰阈值） |

品类阈值见 `category_thresholds.yaml`：`target_acos`、`min_ctr`、`min_cvr` 等按品类区分。

---

## 7. 安全与合规

- **预算护栏**：自动执行有上限，重大变更强制人工；出价下调不低于原值 50%。
- **亚马逊广告政策**：不刷量、不违规定位；否定词不误伤品牌词。
- **审批网关**：默认 `blocked`，杜绝误烧钱 / 误调价。
- **数据隐私**：报表本地快照，外传需显式开启。
- **审计**：每次建议 / 执行留痕，回测可追溯。

---

## 8. 测试

```bash
source .venv/bin/activate
PYTHONPATH=src python -m pytest -q
# 17 passed —— 覆盖：指标计算、诊断规则、建议+否定词挖掘、审批网关、
#             回测吻合率、以及完整 orchestrator.run 链路（含 stub 客户端）
```

---

## 9. 与另两个项目的关系

- **强依赖 sp-api-mcp-server**：所有广告数据来自 `ads_*` 工具；写执行（`ads_campaign_update` / `ads_negative_keyword_create`）经其审批网关。
- 与 **seller-central-reply-assistant** 共享「审批网关 / 护栏 / 人类在环」原则。

---

## 10. 参考资料

- 广告 API：https://advertising.amazon.com/API/docs/en-us/reference
- SP-API：https://developer-docs.amazon/sp-api/docs
- 配套 MCP：https://github.com/middlegold9/sp-api-mcp-server
- 配套客服插件：https://github.com/middlegold9/seller-central-reply-assistant
