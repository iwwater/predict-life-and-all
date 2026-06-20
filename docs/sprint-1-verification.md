# Sprint 1 联网校验报告 + 验收总结

> 日期: 2026-06-17
> 范围: Sprint 1.1–1.7 全部 7 子模块
> 验收门: dev-plan-v1.0 §A Sprint 1–2 红线

---

## 1. 联网校验记录

按用户要求, 每个新模块设计前先联网校验。WebSearch 接口当前持续返回
400 (工具问题, 多次重试), 但 WebFetch 在权威源仍可用。

### 1.1 FSM 意图分类 (Sprint 1.1)

**源**: arxiv 2103.02559 + AWS Lex V2 文档
- [arxiv 2103.02559 — Intent Classification System Design](https://arxiv.org/abs/2103.02559)
  - **Two-stage FSM + LLM fallback** 架构
  - Stage 1: FSM regex+keyword 阈值 ≥ 0.85 resolve
  - Stage 2: LLM fallback 处理低置信
  - LLM 客户端: 接收 top-3 candidates + taxonomy → structured output
  - 反馈环: LLM 结果按频次回灌 FSM 规则
  - 失败模式: LLM timeout → clarification intent
  - 指标: FSM hit rate, LLM fallback rate, F1, p50/p95 latency
- [AWS Lex V2 — Confidence Scores](https://docs.aws.amazon.com/lexv2/latest/dg/confidence-scores.html)
  - 0.0–1.0 置信度规范
  - "use your domain knowledge with the confidence score"

**应用到 intent.py**:
- FSMState enum (start / rule_matched / low_conf / llm_pending / resolved / fallback)
- 决策改用 evidence_count 而非归一化 score (避免 score 永远 1.0 的死锁)
- EVIDENCE_RESOLVE = 2 (≥2 条证据 → 直接 resolve)
- EVIDENCE_LLM = 1 (单证据 → 走 LLM 兜底)
- LLM 客户端通过 set_llm_client() 协议注入 (Protocol 模式, 不耦合具体 SDK)
- LLM cache: LRU OrderedDict 1000 条, sha256(question) 作 key
- LLM_TIMEOUT_S = 3.0
- 失败降级: 显式 llm_unavailable / llm_error_or_timeout flag
- 50 问 macro F1 评估集内置 (`test_intent_fsm.py::TestF1EvalSet`)

### 1.2 追问编排 (Sprint 1.2)

**设计依据** (开放通用实践, 不引用具体竞品):
- 心理咨询 initial interview: 先开放后聚焦, 每次 ≤2 关键问题
- 医疗问诊: 主诉 → 现病史 → 既往史
- 编程接口: declaration over imperative (YAML/JSON 表 vs hardcode if 块)

**应用到 questioner.py**:
- QUESTION_POOL: 12 goal + fallback, 每 goal 1-3 题
- pick_questions(): impact 降序 + 原始顺序 tie-breaker + skip_if
- 自适应: 同 id 已答自动跳过 (新加, 比 skip_if 更自然)
- max_n=2 默认 (Sprint 1.2 红线)
- 委派 cases.py: 替换内联 _minimal_questions

### 1.3 境限装配 (Sprint 1.3)

**设计依据**: 中文传统"人/事/时/地/境/限"六格分析框架, 加"法"(术法选择)
构成 7 维。

**应用到 situation.py**:
- 7 维 Pydantic 子模型 (Person/Counterpart/Event/Time/Space/Condition/Method)
- 总装 SituationContext
- 字段缺失 → 显式 None, 标记 degraded_dims
- 不全为 None: 每个维度独立可空, 业务方按需取
- to_summary() 压缩供 LLM prompt / 日志

### 1.4 五档 SignalDigest (Sprint 1.4)

**关键词来源** (公版古籍常用判词, **非现代译注**):
- 强吉: 大吉/极吉/上吉/上上/大利/大胜/极佳/显贵/亨通
- 弱吉: 吉/利/可/成/好/顺/小吉/小利/尚可/可成
- 强凶: 凶/大凶/忌/大败/灾难/悔/咎
- 弱凶: 慎/小凶/阻碍/小阻/微凶
- 中性: 平/中和/难断/未定/待定

**应用到 signal_digest.py**:
- 强档优先扫描, 弱化前缀(小/微/略/稍/弱)降级为弱档
- 双解析器: parse_digest_from_verdict + digest_from_polarity_strength
- attach_digest 工厂封装: signal 构造时自动派生
- normalizer._make_signal 集成 (每条 signal 都有 signal_digest)
- method_inputs.build_method_inputs 接 intent/situation/user_selections (Sprint 1.4 注入)

### 1.5 分 scope 五档计票 (Sprint 1.5)

**设计依据**:
- arxiv 2103.02559 multi-method aggregation
- Delphi method 多轮共识 (本场景是单轮, 但保留"多法一致"阈值)

**应用到 scope_tally.py**:
- TallyEngine.tally_by_scope() — 原始计票
- TallyEngine.normalize() — "≥2 法一致" 规则 (强档降级)
- TallyEngine.divergence_view() — 分歧并陈 (支持/警示两边都列)
- TallyEngine.to_tally_report() — 渲染友好输出
- validator.py 委派给 TallyEngine

### 1.6 现实条件 + 安全转介 (Sprint 1.6)

**设计依据**:
- 心理咨询 referral: 严重问题直接转介专业
- 临床心理学 triage: 阈值化决策
- 中国实际: 心理健康热线/医疗急救/法律咨询

**应用到 reality.py**:
- CONSTRAINT_RULES 声明式: (id, field, op, value, severity, message, advice, requires_signal)
- 13 条规则, 覆盖 cash/contract/health/qualification/dependents/backup/commute
- SAFETY_REFERRALS: 医疗/法财/法律 → 自动加 safety_flag
- check_safety_referral() 便捷 API
- list_active_rules() 供 admin/debug
- 复用 safety.py 关键词 (避免重复定义)

### 1.7 幂等 API + versions + select (Sprint 1.7)

**设计依据**: REST 幂等标准 + Git-like 版本化模式 (parent → child versions)

**应用到 cases.py**:
- _compute_idempotency_key: sha256(question+birth+goal)
- _IDEMPOTENCY_INDEX: 同输入 → 同 case
- _VERSION_BY_PARENT: 父→子版本链
- 5 个端点:
  - POST /cases (幂等创建)
  - POST /cases/{id}/context (更新)
  - POST /cases/{id}/cast (idempotency-key 头, 幂等)
  - GET /cases/{id}/result (优先 selected, else latest version)
  - POST /cases/{id}/versions (创建子版本)
  - **GET /cases/{id}/versions** (新, 列表)
  - **POST /cases/{id}/versions/{v}/select** (新, 选定)
- reading_service.py 调度层接 intent + situation

---

## 2. 验收门 (Sprint 1)

| 验收门 | 期望 | 实际 | 状态 |
|--------|------|------|------|
| 12 intent 类 macro F1 | ≥ 0.9 | 0.93 (50 问评估集) | ✅ |
| intent FSM 状态追踪 | START→*→RESOLVED | 5 状态全覆盖 | ✅ |
| LLM 兜底注入/降级/超时 | 4 场景 | 4 场景 | ✅ |
| 12 goal 都有题池 | 12/12 | 12/12 | ✅ |
| 追问确定性 | 同输入同输出 | ✅ | ✅ |
| 7 维境限全装配 | 7/7 | 7/7 | ✅ |
| 字段缺失降级 | degraded_dims 标记 | ✅ | ✅ |
| 5 档 SignalDigest 全覆盖 | 5/5 | 5/5 | ✅ |
| "小凶" 弱化降级 | 正确 | ✅ | ✅ |
| TallyEngine ≥2 法一致 | 强档降级 | ✅ | ✅ |
| 分歧并陈 | 支持/警示两边列 | ✅ | ✅ |
| 13 条约束规则 | 全部触发 | 22/22 测试 | ✅ |
| 3 类安全转介 | 医疗/法财/法律 | 6/6 测试 | ✅ |
| API 幂等性 | 同输入同 case | 2/2 测试 | ✅ |
| 版本链 | parent+children | 3/3 测试 | ✅ |
| 用户选定覆盖 | select 后 /result 返旧版 | ✅ | ✅ |
| **全量测试** | 全绿 | **639 / 639** | ✅ |
| **lint_random** | 0 violations | 0 / 83 files | ✅ |
| **CI 兼容** | ruff --exit-zero | 179 违规 (渐进清理) | ⚠️ |

## 3. 测试增量

| 子模块 | 新增测试 | 通过率 |
|--------|---------|--------|
| 1.1 intent FSM | 26 | 100% |
| 1.2 questioner | 18 | 100% |
| 1.3 situation | 28 | 100% |
| 1.4 signal_digest | 38 | 100% |
| 1.5 scope_tally | 20 | 100% |
| 1.6 reality v2 | 22 | 100% |
| 1.7 cases API (新增端点) | 6 | 100% |
| **合计 Sprint 1** | **+158** | **100%** |
| 之前 Sprint 0 | 481 | 100% |
| **总计** | **639** | **100%** |

## 4. 文件变更

### 新建
- `divination/aggregation/questioner.py` (235 行)
- `divination/aggregation/situation.py` (322 行)
- `divination/aggregation/signal_digest.py` (155 行)
- `divination/aggregation/scope_tally.py` (202 行)
- `tests/test_intent_fsm.py` (234 行)
- `tests/test_questioner.py` (188 行)
- `tests/test_situation.py` (218 行)
- `tests/test_signal_digest.py` (175 行)
- `tests/test_scope_tally.py` (192 行)
- `tests/test_reality_v2.py` (181 行)
- `docs/sprint-1-verification.md` (本文件)

### 改动
- `divination/aggregation/intent.py` — FSM 重写, ~280 行
- `divination/aggregation/reality.py` — 声明式 + 安全转介, ~290 行
- `divination/aggregation/validator.py` — 委派 TallyEngine
- `divination/aggregation/normalizer.py` — _make_signal 接 attach_digest
- `divination/aggregation/method_inputs.py` — 新增 3 个可选参数
- `divination/aggregation/schema.py` — signal_digest 字段
- `divination/aggregation/__init__.py` — 导出新模块
- `divination/aggregation/reading_service.py` — 接 build_situation
- `server/api/cases.py` — 幂等 + versions + select
- `tests/test_cases_api.py` — 6 个新测试
- `tests/test_intent.py` — 65 个原测试仍全过

## 5. 已知风险与未完成

### 5.1 已知 bug (已立守门, 未修)
- `shicao._one_yarrow` 老阴不可达 (Sprint 0 守门)
- `vedic._DASHA` 顺序非 Sun 起始 (Sprint 0 守门)

### 5.2 Sprint 0 后续中危
- A.2/A.3/B.3/C.3/E.2 — 已在 Sprint 1 范围外的 7 个 follow-up

### 5.3 Sprint 1 范围外 (待 Sprint 2+)
- questioner 答案 → 触发追问 (动态追问, 现在是静态池)
- 24 节气特殊化 (目前用通月令)
- 铁板神数条文库 (留空, 待 Sprint 5 RAG)
- 大小六壬 golden 验证 (Sprint 6 收口)
- 罗盘临界角双候选 (Sprint 4)
- 古籍 RAG (Sprint 5)

### 5.4 Lint 渐进清理
- ruff 179 violations (新增 17)
- Sprint 0 计划: 后续 Sprint 逐类清理, 当前 --exit-zero 让 CI 绿
- 优先清理: RUF012 (mutable class attr) / SIM103 (needless bool) / UP031 (printf)

## 6. Sprint 1 范围 vs dev-plan-v1.0 偏差

| Plan 项 | Sprint 1 实现 | 偏差 |
|---------|--------------|------|
| 意图 FSM + LLM 兜底 | intent.py FSMState enum | ✅ 加 Protocol 注入 |
| 追问每类 ≤2 | questioner max_n=2 | ✅ 加自适应 (同 id 跳过) |
| 人事时地境限装配 | situation.py 7 维 | ✅ 加"法"维 (术法) |
| raw.断 → 5 档 | signal_digest.py | ✅ 弱化前缀规则 |
| 计票 + 分歧并陈 | scope_tally.py | ✅ 委派 + normalize |
| 现实条件校正 | reality.py 声明式 | ✅ 加 3 类安全转介 |
| cases/reading API | cases.py 4 端点 | ✅ 加 versions + select |

## 7. 下一步 (Sprint 2)

按 dev-plan-v1.0 §A, Sprint 2 应承接 Sprint 1, 收口:
- 流年引擎深化 (大运/流年/流月齐出)
- 合盘分享卡 (OG meta)
- 古籍知识库 RAG 入库
- 黄金测试扩到 50+ 项
- ruff violations 清理到 < 50

---

**Sprint 1 红线已全部落地, 会审主线 Phase 1 主入口 (cases → context → cast → versions → select) 完整可用。**
