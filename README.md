# amazon-ads-review-agent

> Amazon 广告复盘 Agent —— 自动拉取广告报表、诊断异常、给调价与否定词建议，可验证可复盘。
> 运营的 hero 场景，outcome 最硬（ACOS↓、人效↑），最易量化验证、最易讲成面试故事。

> 阶段：**功能设计（Design）**。本仓库当前为端到端功能梳理文档，代码骨架待落地。

---

## 0. 背景与动机

PPC 运营每天：从广告后台拉报表 → 找异常（烧钱无转化、曝光跌、ACOS 超标）→ 调价 / 加否定词 / 调预算。一个运营管数十个活动，手工 1–2h/天，且依赖经验。Agent 把这套「诊断 → 建议 → 执行 → 复盘」自动化，人类只做审批。

**FDE 视角**：这是「可验证、可复盘」的最佳示范——效果可用历史数据回测，策略可沉淀为规则库（高速公路）。对应 FDE 文档 9.4：把现场解法回流成平台能力，越做越轻。

---

## 1. 目标与范围

**Goals**
- 定时拉取多账户 / 多市场广告数据（经 **sp-api-mcp-server** 的 `ads_*` 工具）。
- 自动诊断异常（规则 + LLM 叙事）。
- 生成可执行的优化建议（调价、否定词、预算、暂停）。
- 人类审批后可选自动执行（写接口带护栏）。
- 每日 / 周自然语言复盘报告 + 预警推送（飞书 / 企微）。
- 回测验证 + 策略库沉淀。

**Personas**：PPC 专员、代运营、品牌主。

**Non-goals**
- 不替代最终决策；v1 自动执行默认关闭（仅建议）。
- 不覆盖 DSP（仅 SP / SB / SD）。

---

## 2. 端到端链路

```
[调度触发 cron 每日 09:00 / 周]
   │ 1. 调 sp-api-mcp: ads_profiles_list → 各市场 profileId
   ▼
[数据采集]
   │ 2. ads_performance_report(按天/周) + ads_searchterms_report +
   │    ads_campaigns/adgroups/keywords/targets 快照
   ▼
[归一化 & 指标计算]
   │ 3. 算 ACOS=广告花费/销售额, ROAS, TACOS, CTR, CVR, CPA,
   │    Impression Share, IS lost to budget/rank, 新词有花费无转化
   ▼
[诊断引擎]
   │ 4a. 规则层：ACOS>目标、花费>0 无单、CTR<基准、预算早耗尽、
   │     排名跌、新竞品涌入、预算不足限流
   │ 4b. LLM 层：对异常生成自然语言归因 + 影响估算
   ▼
[建议生成]
   │ 5. 调价(±%)、否定词挖掘(搜索词报表筛无转化词)、
   │    预算再分配、暂停低效、分时段(dayparting)
   ▼
[人类审批网关]
   │ 6. 生成审批卡片(飞书/企微) → 运营确认/修改/驳回
   ▼
[执行(若批准)]
   │ 7. 调 sp-api-mcp 写接口 ads_campaign_update / ads_negativekeyword_create
   │    （护栏：单次预算变更上限、需二次确认）
   ▼
[复盘报告]
   │ 8. NL 报告 + 图表(top movers / ACOS 趋势) + 推送
   ▼
[反馈闭环]
   │ 9. 记录「建议→是否执行→执行后续效果」
   ▼
[策略库沉淀]
      10. 高频有效规则写入规则库 → 复用(高速公路)
```

---

## 3. 功能模块

### 3.1 数据采集
- 多 profile 遍历；报表异步创建 → 轮询 → 下载 gzip。
- 增量：仅拉上次以来数据；快照存本地便于回测。

### 3.2 指标计算
- 核心：ACOS、ROAS、TACOS（总广告销售 / 总销售）、CTR、CVR、CPA。
- 诊断辅助：Impression Share、IS lost to budget/rank、新搜索词、新 ASIN 抢量。

### 3.3 诊断引擎（规则 + LLM）
规则示例：
- ACOS 高于目标阈值且花费 > 中位 → 降出价。
- 搜索词有花费 N 天无转化 → 加否定（exact / phrase）。
- CTR 低于类目基准 → 检查素材 / 关键词相关性。
- 预算在时段早耗尽 → 提预算或 dayparting。
- 排名 / IS 跌 → 加价抢位。
- 新竞品 ASIN 出现在投放目标 → 提示。
- LLM：把触发规则聚合成一段「本周发生了什么、为什么、影响多少」。

### 3.4 建议生成
- 结构化输出：`{entity, action, old, new, rationale, expected_impact, confidence}`。
- 否定词挖掘：从 searchterms 报表筛「花费 ≥ X 且 0 单且无关」→ 候选否定词列表（人工确认）。

### 3.5 审批与执行
- 默认仅建议；开启自动执行需审批 + 护栏（预算变更 ≤ 设定上限/次，出价 ± ≤ 20%）。
- 所有写操作留审计日志。

### 3.6 复盘报告
- NL 摘要 + Top 5 异常 + Top 5 机会 + 图表。
- 推送飞书 / 企微 Webhook。

### 3.7 回测 / 验证
- 读历史快照，模拟「若执行当时建议」的 ACOS / ROAS 走向，对比实际。
- 用于校验诊断准确率（与资深运营标注比对）。

### 3.8 策略库
- 规则版本化；有效规则沉淀为默认；可针对品类定制（3C vs 服饰阈值不同）。

### 3.9 预警
- 实时 / 准实时：ACOS 突增、预算耗尽、某 SKU 销量暴跌 → 即时推送。

---

## 4. 架构
- 编排：LangGraph / 简单 DAG（采集 → 计算 → 诊断 → 建议 → 审批 → 执行 → 报告）。
- 数据：**sp-api-mcp-server**（ads_*）；存储 Postgres / DuckDB（快照、建议、效果）。
- LLM：诊断叙事 + nuanced 建议；规则引擎做确定性判断。
- 调度：cron / 云函数。
- 通知：飞书 / 企微 Webhook。
- 前端（可选）：复盘看板（Streamlit / Gradio）。

---

## 5. 配置
- `.env.example`：`MCP_BASE_URL`, `LLM_*`, `TARGET_ACOS`, `BUDGET_CHANGE_CAP`, `AUTO_EXECUTE=false`, `FEISHU_WEBHOOK`。
- 品类阈值配置：`category_thresholds.yaml`。

---

## 6. 安全与合规
- **预算护栏**：自动执行有上限，重大变更强制人工。
- **亚马逊广告政策**：不刷量、不违规定位；否定词不误伤品牌词。
- **数据隐私**：报表本地存，外传需显式开启。
- **审计**：每次建议 / 执行留痕。

---

## 7. 可验证
- **回测准确**：历史快照上，诊断建议与资深运营实际操作的吻合率（目标 ≥ 85% 一致或更好）。
- **异常召回**：构造含已知异常的数据集，断言被识别。
- **ACOS 影响**：上线后 A/B（采纳组 vs 对照组）看 ACOS / ROAS 改善。
- **人效**：运营日均处理时长下降 %（目标 ≥ 60%）。

---

## 8. 可复盘
- 每周策略复盘会：哪些建议被采纳 / 驳回 → 修规则 / 阈值。
- 指标追踪：ACOS 趋势、采纳率、误报率。
- 策略库版本化，回归测试防退化。

---

## 9. 与另两个项目关系
- 强依赖 **sp-api-mcp-server** 的 `ads_*` 工具（数据源 + 写执行）。
- 与 **seller-central-reply-assistant** 共享「审批网关 / 护栏」理念。

---

## 10. 路线图
- **M1**：采集 + 指标 + 规则诊断 + NL 报告（仅建议）。
- **M2**：否定词挖掘 + 审批网关 + 飞书推送。
- **M3**：回测框架 + 策略库 + 品类阈值。
- **M4**：可选自动执行 + 看板 + 多账户。

---

## 11. 风险与开放问题
- 广告报表异步 + gzip，需健壮轮询与去重。
- 自动执行风险：错调价烧钱 → 护栏 + 默认关闭。
- 归因复杂：ACOS 波动受季节 / 库存影响，诊断需标注「不确定性」。

---

## 12. 参考资料
- 广告 API：https://advertising.amazon.com/API/docs/en-us/reference
- SP-API：https://developer-docs.amazon/sp-api/docs
- 配套 MCP：middlegold9/sp-api-mcp-server
- 配套客服插件：middlegold9/seller-central-reply-assistant
