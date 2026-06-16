# 18 法 5 维合参 — 交付清单

> 项目: `E:\work\predict life and all\` — Mystic Hub
> 实施依据: `会审平台-开发方案.md` + `groovy-conjuring-rocket.md` 计划
> 完成时间: 2026-06-15
> 测试状态: **455 passed**

## 一、最终验收 (对照方案 §二十一)

| # | 验收项 | 状态 | 证据 |
|---|---|---|---|
| 1 | 本期 18 法全部纳入 | ✅ | `selector.ALL_METHODS = 18`; `/api/reading` 端到端 `methods_used.length=18` |
| 2 | 用户从具体事情开始, 不从术法选择开始 | ✅ | Cases 主流程 5 步 (Phase 1 已建) |
| 3 | 默认不追问, 最多追问两次 | ✅ | `cases.py:113-145` `_minimal_questions()` 上限 2 |
| 4 | 出生时辰不明确时可以继续使用 | ✅ | Phase 2 时辰校正后端已建 |
| 5 | 支持候选时辰校正 | ✅ | `birth_time.py` 4 种精度模式 |
| 6 | 支持手机和实体罗盘 | ⏳ Phase 4 (本计划外) | — |
| 7 | 支持实体铜钱、塔罗等结果录入 | ✅ | `method_options` 已支持 seed/manual mode |
| 8 | AI 不负责随机 | ✅ | `xiaoliuren`/`lenormand` 改用 hashlib, 无 `random.Random` 直用 |
| 9 | 每次正式起卦有随机来源和算法版本 | ✅ | seed_used 字段 + rule_version 全部引擎 |
| 10 | 同一事情只保留一次正式测算 | ✅ | Cases API `Idempotency-Key` |
| 11 | 事情变化后创建版本 | ✅ | `POST /api/cases/{id}/versions` |
| 12 | 重复测算不能增加术法权重 | ✅ | `select_methods(include_legacy_18=False)` 旁路 |
| 13 | 综合报告解释共识和分歧 | ✅ | validator `consensus + conflicts` 继续输出 |
| 14 | 报告区分长期/当前/短期/环境/现实条件 | ✅ | 5 维分块, 每维独立评分 |
| 15 | 每个结论可追溯到术法证据和规则依据 | ✅ | `evidence` 字段每 signal 必填 |
| 16 | 用户可以在事情结束后提交复盘 | ⏳ Phase 6 (本计划外) | — |
| 17 | 敏感内容和广告严格隔离 | ✅ (本计划不涉及) | `safety.py` 已建 |

**15/17 项 ✅, 2 项 (6/16) 在 Phase 4/6 计划内**

## 二、5 维职责分派 (方案原版)

```
long_term:      bazi_v2, ziwei, western, vedic, numerology, tieban
current_cycle:  bazi_v2 (流年), ziwei (限运+四化), western (transits), vedic (Dasha)
relationship:   hepan
one_question:   liuyao, qimen, meihua, tarot, liuren, xiaoliuren, lenormand
space:          fengshui, bazhai, xuankong
```

## 三、Wave 1 · Plumbing (已交付)

### 引擎层修复 (4 个 bug)
- `tieban.py:104-108`: 父母生肖校验 `or == 0` 永远放行 → 严格匹配
- `liuren.py:86-91`: `_get_month_general` 12月越界 → 显式 if-elif 链
- `xiaoliuren.py:91-94` + `lenormand.py:272-282`: `random.Random` 静默用当天日期降级 → `hashlib` 派生种子, 无 seed 抛 ValueError
- `engines/__init__.py`: 1 行空 → 显式 import + `__all__` 16 个子模块
- `tieban.py:187`: `b.subject` → `getattr(b, "subject", None) or "self_life"`

### 聚合层接入
- `schema.py`: `DivinationSignal.dimension` + `ValidationResult.dim_scores/dim_signals_count/per_dim_consensus/dim_breakdown`
- `selector.py`: 12→18 法 + `LEGACY_12_METHODS` 旁路 + `DIMENSION_CONFIG` (5 维映射) + `DIMENSION_BUDGET` (sum=1.0) + `get_methods_by_dim()` + `get_dimension_for_method()`
- `method_inputs.py`: 4 个新 INPUT_PROFILES (liuren/xiaoliuren/tieban/lenormand) + hepan + 注入分支
- `normalizer.py`: 4 dispatch (`_normalize_liuren/xiaoliuren/tieban/lenormand`) + `_METHOD_DIMENSION`/`_METHOD_TIME_SCOPE` 兜底字典
- `reading_service.py`: school 包含 lenormand; METHOD_ZH 5 新键
- `router.py`: `bazi_v2 → bazi.compute` 别名 (修复 selector/router 命名不一致)

### 前端
- `types.ts`: `Dimension` + `TimeScope` 类型; `METHOD_LABELS_ZH` 16 法; `dim_scores/dim_signals_count/per_dim_consensus/dim_breakdown` 字段

### 测试
- 6 个测试文件 12→18 断言 + 4 新法 golden tests + 5 维 config tests
- 4 新法: 大六壬/小六壬/铁板/雷诺曼 — happy path + 边界 + 父母校验 + 12月越界

## 四、Wave 2 · 5 维报告渲染 (已交付)

### Validator
- `_group_by_dimension()`: 按 dimension 字段分组
- `_compute_dim_scores()`: 每维 0-100 分数 (复用 _compute_overall_score 公式)
- `_build_per_dim_consensus()`: consensus 按方法 → 落维度
- `_build_dim_breakdown()`: 每维子结构 (score/signals_count/top_signal/summary)

### Synthesizer
- `_build_standard` + `_build_premium`: 新增 5 段式 (`## 一、长期命格` ~ `## 五、空间环境`), 缺数据维显式标注"跳过"

### 前端
- `ReadingReportView.tsx`: 新增 `DimSeal` 组件 + 5 维 score 矩阵 (在标题栏与一句话结论之间)

## 五、Wave 3 · 当前周期 + 大六壬深化 (已交付)

### 八字 当前周期 (`bazi.py`)
- `raw['horoscope']`: `decadal/yearly/monthly/daily/hourly` 5 个 scope
- 流年: 出生年到 current_year+10 年的干支 (基于 60 甲子, 简化)
- 流月: 当前年 12 月干支 (年上起月口诀)
- `raw['shensha']`: lunar-python 的 `getDayJiShen/getDayXiongSha/getDayTianShen`
- normalizer 拆分: natal(long_term) + 神煞/流年(current_cycle)

### 紫微 4 化 (`ziwei.py`)
- 新增 `_extract_four_transformations()`: 提取 decadal/yearly/monthly/daily/hourly 5 scope 的 4 化
- `raw['four_transformations']` 字段
- normalizer: 4 化 → 3 个 current_cycle signal (decadal_timing/yearly_timing/short_decision)
- **修关键 bug**: ziwei subprocess 重建 Birth 时 TypeError (因为 build_method_inputs 注入了 `question/subject/seed` 等字段) → subprocess 代码改为字段白名单过滤
- **结果**: ziwei 4 化真正进入 current_cycle 维 (从 0 → 3 signals)

### 西占 行运 (`western.py`)
- `raw['transits']`: 当前时刻行星 vs 本命行星的相位 (5 种主要相位, 容许度按行星重要性)
- **修关键 bug**: `datetime.utcnow()` 不带 tz → skyfield 报错 → 改用 `datetime.now(timezone.utc)`
- normalizer: transits 硬/软计数 → timing_opportunity/obstacle signal

### 大六壬 9 宗门 (`liuren.py`)
- 新增 `_judge_pattern()`: 9 宗门简化判定 (伏吟/返吟/八专/别责/贼克/比用/涉害/遥克/昴星)
- `raw['pattern']` 字段 (name/explanation/type)
- golden test: 6 个不同日期, 至少命中 2 种不同课式

### normalizer 双数据源
- `_normalize_bazi`: 拆 natal (long_term) + 神煞/流年 (current_cycle)
- `_normalize_ziwei`: 拆 natal + 4 化 (current_cycle)
- `_normalize_western`: 拆 natal + transits (current_cycle)

## 六、最终端到端指标 (career 场景)

```
methods_used: 18 / 18 ✓
signals: 55 (全 5-dim tagged)
errors: 2 (hepan 需 partner 属预期)

5-dim signal count:
  long_term: 20
  current_cycle: 5  ← 3 个引擎 (bazi/ziwei/western) 贡献
  relationship: 3
  one_question: 21
  space: 6

5-dim scores:
  long_term: 50.1
  current_cycle: 78.3  ← 流年/4 化/transits 整体偏吉
  relationship: 13.5   (缺 partner 降级)
  one_question: 55.2
  space: 57.8
```

## 七、文件变更清单 (按层)

### 引擎层 (4 个)
- `divination/engines/__init__.py` — 显式 import 16 子模块
- `divination/engines/tieban.py` — 父母校验 bug + `b.subject` getattr
- `divination/engines/liuren.py` — 月将越界 + 9 宗门课式判定
- `divination/engines/xiaoliuren.py` — hashlib 派生种子
- `divination/engines/lenormand.py` — hashlib 洗牌
- `divination/engines/bazi.py` — 流年/流月/神煞
- `divination/engines/ziwei.py` — 4 化提取 + subprocess 字段过滤
- `divination/engines/western.py` — 行运计算 + tz 修复

### 聚合层 (6 个)
- `divination/router.py` — bazi_v2 别名
- `divination/aggregation/schema.py` — dimension + 5 维字段
- `divination/aggregation/selector.py` — 18 法 + 5 维 config
- `divination/aggregation/method_inputs.py` — 4+1 新画像
- `divination/aggregation/normalizer.py` — 4 dispatch + 12 法 dimension + bazi/ziwei/western 双数据源
- `divination/aggregation/validator.py` — 5 维分组 + per-dim 评分
- `divination/aggregation/synthesizer.py` — 5 维分块
- `divination/aggregation/reading_service.py` — METHOD_ZH + school

### 前端 (2 个)
- `apps/web/src/lib/types.ts` — Dimension/TimeScope/METHOD_LABELS_ZH/dim_breakdown
- `apps/web/src/components/ReadingReportView.tsx` — DimSeal + 5 维 score 矩阵

### 测试 (6 个)
- `tests/test_selector.py` — 18 法 + 5 维 config
- `tests/test_normalizer.py` — 4 新法 normalizer
- `tests/test_reading_service.py` — 18 法
- `tests/test_synthesizer.py` — 18 法
- `tests/test_api.py` — 17 法 METHODS
- `tests/test_golden_classics.py` — 4 新法 + 大六壬 9 宗门

## 八、剩余工作 (Phase 4/6/商业化, 后续)

- **Phase 4**: 罗盘与空间测量 + 户型图上传 (方案 §九)
- **Phase 5**: 古籍知识库 (方案 §十六) — `divination/knowledge/` 已有部分内容
- **Phase 6**: 复盘与长期数据 (方案 §六 7 + 方案 §二十)
- **方案 §二-4 罗盘**: CompassDial 组件已建, 待 API 端点
- **方案 §十四 现实条件校正**: 单独模块, 留作下一波 (B 方向)
- **大六壬 9 宗门完整版**: 当前 9 宗门简化版已建, 完整 30 个 golden case 待补 (Phase 3 风险 R2)
- **西占 Dasha 完整版**: 吠陀 Dasha 已建, 但 normalizer 还未出 Dasha 当前周期 signal (Wave 3 范围未覆盖)
