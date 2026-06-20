# Sprint 2 验收报告 (2026-06-17)

> 范围: dev-plan-v1.0 §A Sprint 3 (流年 + 合盘分享卡)
> 完成度: 4/4 子任务 + 1 验收

---

## 1. 子任务完成情况

| # | 子任务 | 文件 | 测试 | 状态 |
|---|--------|------|------|------|
| 2.1 | bazi 流年/流月/大运 深化 | `divination/engines/bazi.py` + `aggregation/normalizer.py` | 13 项 golden | ✅ |
| 2.2 | western 三通道 (transits/progressions/returns) | `divination/engines/western.py` + normalizer | 15 项 | ✅ |
| 2.3 | ziwei 大限/流年/流月 限运 | `aggregation/normalizer.py` (引擎已具备 4 化) | 8 项 | ✅ |
| 2.4 | 合盘分享卡 server API | `server/api/hepan_share.py` + main.py 集成 | 12 项 | ✅ |
| 2 验 | golden + 端到端 | 多测试文件 | 106 golden | ✅ |

## 2. Sprint 2 新增/改动

### 新建
- `tests/test_bazi_liunian_golden.py` (13 项 — 60 甲子 baseline + 流月 + 大运)
- `tests/test_western_three_channels.py` (15 项 — transit/progression/return)
- `tests/test_ziwei_limiyun.py` (8 项 — 大限+流年+流月 4 化)
- `tests/test_hepan_share.py` (12 项 — 12 生肖 + 端到端 share)
- `server/api/hepan_share.py` (200 行 — OG meta + share card data)
- `docs/sprint-2-verification.md` (本文件)

### 改动
- `divination/engines/bazi.py` — 加 `horoscope.raw.{current_year, yearly, monthly, current_dayun}`
- `divination/engines/western.py` — 加 `_find_transits` / `_find_progressed_aspects` / `_solar_return_moment`
- `divination/aggregation/normalizer.py` — 大运+流月 bazi signal / 太阳返照 western signal / 流月独立 ziwei signal
- `divination/aggregation/normalizer.py` — SIGNAL_KEYS 加 `current_cycle_dasha` + 3 个 `prog_timing_*`
- `server/main.py` — 集成 hepan_share router
- `tests/test_normalizer.py` — 更新 key count 期望 (28 → 32)

## 3. 关键设计

### 3.1 bazi 流年/流月/大运
- 引擎用 lunar-python 反查 ±60 年 60 甲子
- 当前大运: 用 birth.gender 取顺/逆排, timeline 匹配
- 极性: 天干 5 合/克 (生日=positive, 克日=negative)
- Golden: 1984 甲子、1998 戊寅、2014 甲午、2026 丙午 (公版 60 甲子)

### 3.2 western 三通道
- **行运 transits**: 当前天空 vs 本命, 容许度 ±2°, 跨行星 + 自相位
- **次限 progressions**: 1日=1年, progressed_date = birth + age_years
- **太阳返照 solar_return**: 太阳回到本命位置 (年主题), 12h 细化精度 < 1°
- 4 化映射: 刑(90)/冲(180) = hard, 合(0)/六合(60)/拱(120) = soft

### 3.3 ziwei 限运
- 引擎已输出 decadal/yearly/monthly/daily/hourly 4 化 (大限+流年+流月+流日+流时)
- normalizer 大限/流年各 1 signal, 流月独立 1 signal
- 3 个 current_cycle signal (满足 plan 红线 ≥3)

### 3.4 合盘分享卡
- OG meta: title/description/image/url (移动端可读)
- 卡片数据: 双方生肖年 (12 生肖公版映射), 3 条 key signals (按 strength 排序), 5 维 judgment, tally summary
- 限制: 仅 hepan/compatibility/relationship 类型 case 可分享 (400 拦截其他)
- 状态: 需 cast 完成 (409 拦截 draft)
- 12 生肖 baseline: 1900 鼠 / 1990 马 / 2000 龙 / 2024 龙

## 4. 验收门 (Sprint 2)

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

## 5. Sprint 2 增量测试

| 类别 | 新增 | 累计 |
|------|------|------|
| 之前 Sprint 0+1 | — | 639 |
| Sprint 2.1 bazi | 13 | 652 |
| Sprint 2.2 western | 15 | 667 |
| Sprint 2.3 ziwei | 8 | 675 |
| Sprint 2.4 hepan share | 12 | 687 |

## 6. 已知问题与下步

### 6.1 Sprint 2 范围外
- apps/web 分享页 (前端, 需用户态)
- 真实 PNG 生成 (当前 OG image URL 占位, 前端动态 SVG)
- 二维码生成 (前端 JS 库)

### 6.2 Lint 渐进
- ruff 183 violations (新增 4) — 仍 --exit-zero
- 优先: RUF012 / SIM103 / UP031 / UP037 (12 项可自动 fix)

### 6.3 Sprint 3 (dev plan: 罗盘 + 空间)
- 罗盘三通道 (磁北/真北/iOS 权限)
- 临界角 < 5° → 双候选 + 复测
- 户型图按扇区法归宫

---

**Sprint 2 收口: 流年主线 (八字/西占/紫微) 全部齐出, 合盘分享卡 server 端就绪。前端页面 (apps/web) 待 Sprint 3 同步开发。**
