# Sprint 1 + 2 验收总结

> 日期: 2026-06-17 (Sprint 1.7 红线落地完成日)
> 合并自 `sprint-1-verification.md` + `sprint-2-verification.md`
> 范围: dev-plan-v1.0 §A Sprint 1–2 红线

---

## 一、Sprint 1 · 七子模块全绿 (2026-06-17)

### 1.1 联网校验记录

按用户要求, 每个新模块设计前先联网校验。WebSearch 接口当前持续返回
400 (工具问题, 多次重试), 但 WebFetch 在权威源仍可用。

**Sprint 1.1 FSM 意图分类**
- 源: arxiv 2103.02559 + AWS Lex V2 文档
- arxiv 2103.02559: Two-stage FSM + LLM fallback 架构,Stage 1 FSM regex+keyword ≥0.85 resolve,Stage 2 LLM fallback
- AWS Lex V2: 0.0–1.0 置信度规范
- **应用到 intent.py**: FSMState enum (5 状态) / evidence_count 决策 / LLM 协议注入 / LRU cache 1000 条 / LLM_TIMEOUT_S = 3.0 / 50 问 macro F1 评估集
- 验证: FSM hit rate / LLM fallback rate / F1 / p50/p95 latency

**Sprint 1.2 追问编排**
- 设计依据: 心理咨询 initial interview + 医疗问诊 + 编程 declaration over imperative
- **应用到 questioner.py**: 12 goal × 1-3 题 / 委派 cases.py / 自适应 skip / max_n=2

**Sprint 1.3 境限装配**
- 设计依据: "人/事/时/地/境/限" + "法" 7 维
- **应用到 situation.py**: 7 维 Pydantic / degraded_dims / to_summary()

**Sprint 1.4 五档 SignalDigest**
- 关键词来源: 公版古籍常用判词 (非现代译注)
- **应用到 signal_digest.py**: 强档优先 / 弱化前缀规则 / 双解析器 / attach_digest 工厂 / normalizer 集成

**Sprint 1.5 分 scope 五档计票**
- 设计依据: arxiv 2103.02559 multi-method aggregation + Delphi method
- **应用到 scope_tally.py**: tally_by_scope / normalize ≥2 法一致 / divergence_view 并陈 / to_tally_report

**Sprint 1.6 现实条件 + 安全转介**
- 设计依据: 心理咨询 referral + 临床心理学 triage + 中国实际热线
- **应用到 reality.py**: CONSTRAINT_RULES 13 条 / SAFETY_REFERRALS 3 类 / check_safety_referral / list_active_rules

**Sprint 1.7 幂等 API + versions + select**
- 设计依据: REST 幂等标准 + Git-like 版本化模式
- **应用到 cases.py**: sha256 idempotency key / version 链 / 5 个端点 + GET versions + POST versions/{v}/select
- reading_service.py 接 intent + situation

### 1.2 Sprint 1 验收门

| 验收门 | 期望 | 实际 | 状态 |
|--------|------|------|------|
| 12 intent 类 macro F1 | ≥ 0.9 | 0.93 (50 问) | ✅ |
| intent FSM 状态追踪 | START→*→RESOLVED | 5 状态全覆盖 | ✅ |
| LLM 兜底注入/降级/超时 | 4 场景 | 4 场景 | ✅ |
| 12 goal 都有题池 | 12/12 | 12/12 | ✅ |
| 7 维境限全装配 | 7/7 | 7/7 | ✅ |
| 5 档 SignalDigest 全覆盖 | 5/5 | 5/5 | ✅ |
| TallyEngine ≥2 法一致 | 强档降级 | ✅ | ✅ |
| 13 条约束规则 | 全部触发 | 22/22 测试 | ✅ |
| 3 类安全转介 | 医疗/法财/法律 | 6/6 测试 | ✅ |
| API 幂等性 | 同输入同 case | 2/2 测试 | ✅ |
| 用户选定覆盖 | select 后 /result 返旧版 | ✅ | ✅ |
| **全量测试** | 全绿 | **639 / 639** | ✅ |
| **lint_random** | 0 violations | 0 / 83 files | ✅ |
| **CI 兼容** | ruff --exit-zero | 179 违规 (渐进清理) | ⚠️ |

### 1.3 Sprint 1 文件变更

**新建**
- `divination/aggregation/questioner.py` (235 行)
- `divination/aggregation/situation.py` (322 行)
- `divination/aggregation/signal_digest.py` (155 行)
- `divination/aggregation/scope_tally.py` (202 行)
- `tests/test_intent_fsm.py` (234 行) + test_questioner/test_situation/test_signal_digest/test_scope_tally/test_reality_v2.py
- `docs/sprint-1-verification.md` (已合并入本文件)

**改动**
- `divination/aggregation/intent.py` — FSM 重写 (~280 行)
- `divination/aggregation/reality.py` — 声明式 + 安全转介 (~290 行)
- `divination/aggregation/validator.py` — 委派 TallyEngine
- `divination/aggregation/normalizer.py` — _make_signal 接 attach_digest
- `divination/aggregation/method_inputs.py` — 3 个新参数
- `divination/aggregation/schema.py` — signal_digest 字段
- `server/api/cases.py` — 幂等 + versions + select
- `tests/test_cases_api.py` — 6 个新测试

### 1.4 Sprint 1 已知风险

**Sprint 0 已知 bug (已立守门, 未修)**
- `shicao._one_yarrow` 老阴不可达
- `vedic._DASHA` 顺序非 Sun 起始

**Sprint 1 范围外 (Sprint 2+ 待办)**
- questioner 答案 → 触发追问 (动态追问)
- 24 节气特殊化 (目前用通月令)
- 铁板神数条文库 (留空, 待 Sprint 5 RAG)
- 大小六壬 golden 验证 (Sprint 6 收口)
- 罗盘临界角双候选 (Sprint 4)
- 古籍 RAG (Sprint 5)

**Lint 渐进**
- ruff 179 violations (新增 17), --exit-zero 让 CI 绿
- 优先清理: RUF012 / SIM103 / UP031

### 1.5 Sprint 1 范围 vs dev-plan-v1.0 偏差

| Plan 项 | Sprint 1 实现 | 偏差 |
|---------|--------------|------|
| 意图 FSM + LLM 兜底 | intent.py FSMState enum | ✅ 加 Protocol 注入 |
| 追问每类 ≤2 | questioner max_n=2 | ✅ 加自适应 (同 id 跳过) |
| 人事时地境限装配 | situation.py 7 维 | ✅ 加"法"维 (术法) |
| raw.断 → 5 档 | signal_digest.py | ✅ 弱化前缀规则 |
| 计票 + 分歧并陈 | scope_tally.py | ✅ 委派 + normalize |
| 现实条件校正 | reality.py 声明式 | ✅ 加 3 类安全转介 |
| cases/reading API | cases.py 4 端点 | ✅ 加 versions + select |

---

## 二、Sprint 2 · 流年主线 + 合盘分享卡 (2026-06-17)

> 范围: dev-plan-v1.0 §A Sprint 3 (流年 + 合盘分享卡)
> 完成度: 4/4 子任务 + 1 验收

### 2.1 子任务完成情况

| # | 子任务 | 文件 | 测试 | 状态 |
|---|--------|------|------|------|
| 2.1 | bazi 流年/流月/大运 深化 | `divination/engines/bazi.py` + `aggregation/normalizer.py` | 13 项 golden | ✅ |
| 2.2 | western 三通道 (transits/progressions/returns) | `divination/engines/western.py` + normalizer | 15 项 | ✅ |
| 2.3 | ziwei 大限/流年/流月 限运 | `aggregation/normalizer.py` (引擎已具备 4 化) | 8 项 | ✅ |
| 2.4 | 合盘分享卡 server API | `server/api/hepan_share.py` + main.py 集成 | 12 项 | ✅ |
| 2 验 | golden + 端到端 | 多测试文件 | 106 golden | ✅ |

### 2.2 Sprint 2 关键设计

**bazi 流年/流月/大运**
- 引擎用 lunar-python 反查 ±60 年 60 甲子
- 当前大运: 用 birth.gender 取顺/逆排, timeline 匹配
- 极性: 天干 5 合/克 (生日=positive, 克日=negative)
- Golden: 1984 甲子、1998 戊寅、2014 甲午、2026 丙午 (公版 60 甲子)

**western 三通道**
- **行运 transits**: 当前天空 vs 本命, 容许度 ±2°, 跨行星 + 自相位
- **次限 progressions**: 1日=1年, progressed_date = birth + age_years
- **太阳返照 solar_return**: 太阳回到本命位置 (年主题), 12h 细化精度 < 1°
- 4 化映射: 刑(90)/冲(180) = hard, 合(0)/六合(60)/拱(120) = soft

**ziwei 限运**
- 引擎已输出 decadal/yearly/monthly/daily/hourly 4 化
- normalizer 大限/流年各 1 signal, 流月独立 1 signal
- 3 个 current_cycle signal (满足 plan 红线 ≥3)

**合盘分享卡**
- OG meta: title/description/image/url (移动端可读)
- 卡片数据: 双方生肖年 (12 生肖公版映射), 3 条 key signals, 5 维 judgment, tally summary
- 限制: 仅 hepan/compatibility/relationship 类型 case 可分享 (400 拦截其他)
- 状态: 需 cast 完成 (409 拦截 draft)
- 12 生肖 baseline: 1900 鼠 / 1990 马 / 2000 龙 / 2024 龙

### 2.3 Sprint 2 验收门

| 验收门 | 期望 | 实际 | 状态 |
|--------|------|------|------|
| 60 甲子 baseline | 1984 甲子 / 1998 戊寅 / 2014 甲午 | 6 项 golden | ✅ |
| 大运 signal 派生 | current_cycle dasha key | ✅ | ✅ |
| 流月 signal 派生 | timing_transition (含"流月"字样) | ✅ | ✅ |
| Western transits | 容许度 ±2°, 命中 0-N | ✅ | ✅ |
| Progressions | progressed_date = birth + age_years | ✅ | ✅ |
| Solar return | 精度 < 1° | ✅ (12h 细化) | ✅ |
| Ziwei 大限+流年+流月 ≥3 signal | ✓ | ✅ | ✅ |
| 合盘 share API | 5 段结构 (og/card/disclaimer) | ✅ | ✅ |
| 12 生肖 baseline | 6 公版年 | ✅ | ✅ |
| 仅 hepan/compatibility 分享 | 400 拦截其他 | ✅ | ✅ |
| share 需 cast | 409 拦截 draft | ✅ | ✅ |
| **全量测试** | 全绿 | **687 / 687** | ✅ |
| **lint_random** | 0 violations | 0 / 84 files | ✅ |
| **golden tests** | ≥ 50 项 | 106 (golden + 限运 + 流年) | ✅ |

### 2.4 Sprint 2 文件变更

**新建**
- `tests/test_bazi_liunian_golden.py` (13 项 — 60 甲子 baseline + 流月 + 大运)
- `tests/test_western_three_channels.py` (15 项)
- `tests/test_ziwei_limiyun.py` (8 项)
- `tests/test_hepan_share.py` (12 项)
- `server/api/hepan_share.py` (200 行)
- `docs/sprint-2-verification.md` (已合并入本文件)

**改动**
- `divination/engines/bazi.py` — `horoscope.raw.{current_year, yearly, monthly, current_dayun}`
- `divination/engines/western.py` — `_find_transits` / `_find_progressed_aspects` / `_solar_return_moment`
- `divination/aggregation/normalizer.py` — 大运+流月 bazi signal / 太阳返照 western signal / 流月独立 ziwei signal
- `divination/aggregation/normalizer.py` — SIGNAL_KEYS 加 `current_cycle_dasha` + 3 个 `prog_timing_*`
- `server/main.py` — 集成 hepan_share router
- `tests/test_normalizer.py` — 更新 key count 期望 (28 → 32)

### 2.5 Sprint 2 范围外

- apps/web 分享页 (前端, 需用户态)
- 真实 PNG 生成 (当前 OG image URL 占位, 前端动态 SVG)
- 二维码生成 (前端 JS 库)
- ruff violations 清理 (新增 4, 仍 --exit-zero)
- Sprint 3 (罗盘 + 空间): 磁北/真北/iOS 权限 + 临界角双候选 + 户型图扇区法

---

## 三、Sprint 1+2 累计指标

| 类别 | Sprint 1 | Sprint 2 | 累计 |
|------|----------|----------|------|
| 新增测试 | 158 | 48 | 206 |
| 总测试数 | 639 | 687 | 687 |
| golden 测试 | — | 106 | 106 |
| lint_random violations | 0 | 0 | 0 |
| ruff violations | 179 | 183 | 183 |

**Sprint 1+2 收口**:
- Sprint 1: 7 子模块 (intent FSM/questioner/situation/signal_digest/scope_tally/reality v2/cases API)
- Sprint 2: 4 子模块 (bazi 流年 / western 三通道 / ziwei 限运 / 合盘分享卡)
- **会审主线 Phase 1 主入口 (cases → context → cast → versions → select) 完整可用**
- **流年主线 (八字/西占/紫微) 全部齐出, 合盘分享卡 server 端就绪**
- apps/web 分享页待 Sprint 3 同步开发

---

*文档生成: 2026-06-17 (合并日 2026-06-20) · sprint-1-verification.md + sprint-2-verification.md 整合*
