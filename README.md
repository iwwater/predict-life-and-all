# 玄枢 Mystic Hub · 中西方统一算命引擎

> **19 术法全覆盖** · 统一接口 `compute(method, birth, **kw)` · 后端 FastAPI + 前端 React + Vite
>
> 西方走 B 路（skyfield + 自算星座/相位/宫位），全程 MIT/BSD，零 AGPL，可闭源商用。

---

## 一、19 术法（命 / 卜 / 相 / 山 四类）

| 类别 | 术法 | 引擎 | 文献深度 |
|------|------|------|---------|
| **命·东方** | 八字(bazi / bazi_v2) · 紫微(ziwei) · 数字命理(numerology · 毕达哥拉斯+姓名学) | `divination/engines/bazi*.py` | ★★★★★ |
| **命·西方** | 西方占星(western · 行运/次限/太阳返照) · 吠陀(vedic · Lahiri + Yogas) | `divination/engines/western.py vedic.py` | ★★★★☆ |
| **卜·东方** | 奇门(qimen · 72 局 + 飞盘) · 大六壬(liuren · 720 课) · 六爻(liuyao) · 梅花(meihua) · 小六壬(xiaoliuren) · 蓍草(shicao) · 铁板神数(tieban) | `divination/engines/qimen.py liuren.py ...` | ★★★★★ |
| **卜·西方** | 塔罗(tarot · 78 张 + Fool's Journey) · 雷诺曼(lenormand · 36 张) | `divination/engines/tarot.py lenormand.py` | ★★★★☆ |
| **相·辅助** | 称骨(chenggu) · 解梦(dream · 138 条) · 合盘(hepan) | `divination/engines/*.py` | ★★★☆☆ |
| **山·风水** | 八宅(bazhai) · 玄空(xuankong) · 罗盘采集(compass · 24 山 + declination + 连续采样) | `divination/engines/{bazhai,xuankong,compass}.py` | ★★★★☆ |

完整说明见 [`docs/ALGORITHM_IMPROVEMENT_PLAN.md`](docs/ALGORITHM_IMPROVEMENT_PLAN.md)

---

## 二、已深度验证（实测，非声称）

- ✅ **八字**（lunar-python）+ **真太阳时校正**（经度差 + 均时差，EoT 对 5 个已知日期误差 <0.1 分钟）
- ✅ **紫微**（py-iztro）
- ✅ **西方行星黄经**：修正两处 bug 后，二分二至误差 0.000°
- ✅ **上升点**：三张盘反推地平高度均 ≈0.000° 且在东方
- ✅ **Placidus 宫位**：半弧自自治在 5 个纬度（含赤道/高纬奥斯陆）验证，误差 <0.01°
- ✅ **风水·玄空飞星**：八运子山午向=双8到向、丑/未山=旺山旺向，合《沈氏玄空学》；下元九运正确
- ✅ **风水·八宅**：1990 男=坎命东四（吉方坎离震巽），合《八宅明镜》
- ✅ **历史夏令时**：zoneinfo 正确套用 1986–1991 中国夏令时（八字时柱常见错误来源）
- ✅ **罗盘·24 山**：中心/边界/临界角双候选 <5°，WMM 磁偏角估算（中国/日本/北美）
- ✅ **跨系统交叉验证**：Bazi × Ziwei × Western 加权集成，agreement matrix 0-1 置信度
- ✅ **三通道西占推运**：行运 / 次限推运 / 太阳返照（secondary progressions day=year）

### 深度调查修正的真 bug

1. `ecliptic_latlon()` 返回 (纬度, 经度, 距离) —— 经度在第 2 位（原代码取反成黄纬）。
2. 必须传 `epoch=t` 用当日黄道（回归黄道）；否则按 J2000 差一个岁差量（今约 0.34°，逐年增大）。
3. 均时差不能用视黄经，须用太阳平黄经线性式（原草稿差 5–7 分钟）。
4. `true_solar_time` 必须用时区**标准经度**查表，不能从 `utcoffset` 反推（1990 中国夏令时会污染结果）。

---

## 三、用法

### 3.1 Python 直接调用

```python
from divination import Birth, compute, compute_all
b = Birth(1990, 5, 15, 8, 30, gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
compute("bazi", b)
compute("ziwei", b)
compute("qimen", b)
compute("western", b)
compute_all(["bazi", "western"], b)   # 中西一起算
```

### 3.2 HTTP API

```bash
# 单法
curl -X POST http://127.0.0.1:8000/api/compute \
  -H "Content-Type: application/json" \
  -d '{"method": "bazi", "birth": {"year":1990,"month":5,"day":15,"hour":8,"minute":30}}'

# 多法 + 交叉验证
curl -X POST http://127.0.0.1:8000/api/compute/multi \
  -H "Content-Type: application/json" \
  -d '{"methods": ["bazi_v2","ziwei","western"], "birth": {...}, "subject": "self_life"}'

# 时辰校准（生时不确定时反推）
curl -X POST http://127.0.0.1:8000/api/calibrate/hour -d '{"birth": {...}}'

# 古籍书单
curl http://127.0.0.1:8000/api/knowledge/books?method=bazi&verified_only=true
```

完整端点见 [`docs/CROSS_VALIDATION_COMPARISON.md`](docs/CROSS_VALIDATION_COMPARISON.md)

### 3.3 前端

```bash
cd apps/web && npm run dev
# → http://127.0.0.1:5173
```

主路径：`/`（首页）· `/m/{method}`（19 个专页）· `/cases`（问事档案）· `/compass`（罗盘采集）· `/dream`（解梦）· `/knowledge`（古籍知识库）· `/heshen`（合参）

---

## 四、模块化架构

```
divination/
├── contracts.py          # 统一 Birth + ChartResult 数据契约
├── router.py             # 19 engines 统一调度入口
├── engines/              # 19 术法引擎
│   ├── bazi.py / bazi_v2.py / ziwei.py
│   ├── qimen.py / liuren.py / liuyao.py / meihua.py / xiaoliuren.py
│   ├── shicao.py / tieban.py / chenggu.py
│   ├── western.py / vedic.py / tarot.py / lenormand.py / numerology.py
│   ├── bazhai.py / xuankong.py / fengshui.py / compass.py
│   ├── dream.py / hepan.py
│   ├── cross_validator.py / hour_calibrator.py
│   ├── shensha.py / wuxing.py / yijing.py / ...
├── aggregation/          # 12 术法聚合 (selector / validator / synthesizer / safety / llm_prompt)
├── knowledge/            # 古籍知识库 (books.py / classical.py)
├── data/                 # 静态数据 (tieban_verses / qimen_jiu_jun / shensha_data / ...)
├── interpret/            # LLM 解读层 (盘面→护栏→LLM→护栏→解读)
└── solartime.py / astro_math.py / synastry.py

server/
├── main.py               # FastAPI 入口
├── api/                  # 路由 (compute / cases / almanac / compass / daily / dream / knowledge / ...)
├── llm/                  # LLM client + prompts + references (60+ 古籍)
└── llm/references/       # 68 个 RAG 参考文件 (公版)

apps/web/                 # React 19 + Vite + TypeScript
├── src/pages/            # Home / Cases / CompassPage / DreamPage / Knowledge / methods/*
├── src/components/       # Layout / Sidebar / ReadingReportView / CompassDial / ...
└── src/lib/              # api.ts / types.ts / i18n / store/ (birth + readingHistory)
```

---

## 五、测试与质量

```bash
# 完整 pytest 套件 (2100+ 项)
python -m pytest tests/ -q

# 仅 compass / 罗盘
python -m pytest tests/test_compass.py -v

# 黄金案例（古籍定数 / 天文基准）
python -m pytest tests/test_golden_classics.py tests/test_golden_astronomy.py -v

# TypeScript 检查
cd apps/web && npx tsc --noEmit

# 生产构建
cd apps/web && npm run build
```

**当前状态**: 2150 passed / 0 failed（六神 + 称骨/铁板 + 塔罗三系统 + 灵签回归）· TypeScript 零错 · 0 flaky
**任何依赖升级必须全绿才可并入。**

---

## 六、文档索引

### 战略 & 调研
- [`docs/ALGORITHM_IMPROVEMENT_PLAN.md`](docs/ALGORITHM_IMPROVEMENT_PLAN.md) — 19 术法改进优先级矩阵 + 工时估算
- [`docs/COMPETITOR_ANALYSIS_2026.md`](docs/COMPETITOR_ANALYSIS_2026.md) — 8 个 AI 玄学项目竞品调研 + Top 10 改进点
- [`docs/CROSS_VALIDATION_COMPARISON.md`](docs/CROSS_VALIDATION_COMPARISON.md) — 与 dzcmemory-web/bazi-ziwei-skill 全面对比
- [`docs/dev-plan-v1.0-ancient-optimization-compass.md`](docs/dev-plan-v1.0-ancient-optimization-compass.md) — 古籍优化 + 罗盘 v1.0 规划

### 算法 & 文献
- [`docs/CLASSICAL_SOURCES.md`](docs/CLASSICAL_SOURCES.md) — 18 法 × 古籍 × 验证状态（60+ 本）
- [`docs/phase-delivery-18methods-5dim.md`](docs/phase-delivery-18methods-5dim.md) — 18 法 5 维度交付方案
- [`docs/phase1-case-flow.md`](docs/phase1-case-flow.md) / [`phase2-birth-time-rectification.md`](docs/phase2-birth-time-rectification.md)

### 伦理 & 合规
- [`docs/ETHICS.md`](docs/ETHICS.md) — 7 项解读原则 + 4 类警示语 + 3 层护栏

### 验证 & 交接
- [`docs/sprint-1-verification.md`](docs/sprint-1-verification.md) / [`docs/sprint-2-verification.md`](docs/sprint-2-verification.md)
- [`docs/dev-log-2026-06-15.md`](docs/dev-log-2026-06-15.md) — 工作日志
- [`docs/SESSION_2026-06-21.md`](docs/SESSION_2026-06-21.md) — **当前** session handoff（六神测试解 skip + 文档同步）
- [`docs/SESSION_2026-06-20.md`](docs/SESSION_2026-06-20.md) — Sprint 4 状态 + docs 收口（已由 6.21 更新）
- [`docs/SESSION_2026-06-19.md`](docs/SESSION_2026-06-19.md) — Sprint 3 + 6.18 P0 全绿

### 部署
- [`docs/DEPLOY.md`](docs/DEPLOY.md) — Cloudflare Pages + Docker 部署指南

---

## 七、仍是 TODO

### P1 — 体验优化
- ✅ 罗盘：WMM2025 磁偏角升级（高斯球谐展开 N=12, 数据源 NCEI）— Sprint 4.3
- ✅ 紫微：SVG 4 种盘可视化（传统方盘 / 现代轮盘 / 宫位网格 / 星曜地图）— Sprint 4
- ✅ 塔罗：密码学安全抽牌（HMAC-SHA3-256 承诺方案 + NIST DRBG）— Sprint 4.2
- ✅ 连续采样 UX：实时质量指示器 + 连续采样进度 / 精度反馈 — Sprint 4

### P2 — 深度升级
- ✅ 六爻：六神（青龙/朱雀/勾陈/螣蛇/白虎/玄武）+ 伏神/飞神 + 世应冲合 — 6.21 测试解 skip
- ✅ 紫微：飞星四化集成 + 宫位飞化 — Sprint 4.1
- ✅ 奇门：阴/阳遁自动判定 + 多盘式（时/日/月/年 + 转/飞 + 拆补/茅山）— 6.17
- ✅ 铁板：太玄数公式精校 + 邵雍本 / 铁冠道人本双流派切换 — 6.21 回归锁定
- ✅ 西占：Aspects 网格 + 相位影响力（容许度差异化）+ 月亮交点 / Lilith — Sprint 4

### P3 — 探索性
- ✅ 紫微小限 + HTML/React 交互盘 — Sprint 4
- ✅ 塔罗三系统融合（韦特 + 托特 + 现代心理）：engine/API/起卦页/专页/会审表单已接入 — 6.21
- ✅ 观音灵签 / 关帝灵签：`qian` engine + `/api/compute` + `/m/qian` + 结果盘面已接入；基础条目分层标注 — 6.21
- ✅ Placidus 极区（|lat|>66°）专门处理：自动回退等宫 + warning — Sprint 4

完整计划见 [`docs/ALGORITHM_IMPROVEMENT_PLAN.md`](docs/ALGORITHM_IMPROVEMENT_PLAN.md)

---

## 八、伦理与边界

> **本平台所有术法均属"传统象征视角的参考", 不构成科学预测或命运判决。**
> 排盘是工具, **不应替代个人的判断、努力与现实行动**。
> 解读须温和、尊重、有疗愈价值, 避免绝对化、恐吓化、消费焦虑。

详见 [`docs/ETHICS.md`](docs/ETHICS.md) · 解读层 7 项原则 + 4 类警示语模板 + 3 层护栏。

---

*最近更新：2026-06-21（六神/称骨/铁板/塔罗/灵签回归 · 2150/2150 测试通过）*
