# 玄枢 Mystic Hub

> 中西融通玄学排盘 + AI 解读 Web App  
> 14 种术数统一接口 / 纯 MIT+BSD / 零 AGPL / 可闭源商用

**v2 前端重构** — 一法一专页：每法独立闭环页 (`/m/{method}`)，用户主动将盘面收入「卷宗」后在 `/heshen` 发起合参。

- **后端**: FastAPI 单体,核心引擎层 `divination/` (lunar-python + py-iztro + 自实现奇门 + skyfield + 自算)
- **聚合层**: 多法统一调度、信号标准化、加权交叉验证、三档报告生成、LLM Prompt 构建
- **安全层**: 危机词拦截、医疗/法律/投资敏感领域降级、绝对化表达过滤、日志脱敏
- **前端**: React 18 + Vite 5 + TypeScript + Tailwind 3,宣纸墨色主题,响应式 Web
- **AI 解读**: 用户在前端自备 OpenAI / Claude / Gemini / DeepSeek Key,后端只暴露 Prompt 模板
- **覆盖**: 14 大术数 — 八字、紫微、奇门、六爻、梅花、称骨、八宅、玄空飞星、合盘、西方占星、吠陀占星、塔罗、数字命理、大六壬 / 铁板神数 / 雷诺曼（引擎就绪，前端待接入）

> 免责声明:本平台为传统文化与自我反思工具,所有解读**非科学预测**,不构成医疗 / 法律 / 财务 / 投资建议。涉及健康、法律、投资的决定请咨询专业人士。

---

## 快速开始

### 本地开发

```bash
# 1) Python 后端
pip install -r requirements_divination.txt    # 或 uv sync
cd "E:\work\predict life and all"

# 2) 启动后端 (端口 8000)
python -m uvicorn server.main:app --reload --port 8000

# 3) 启动前端 (端口 5173, 自动代理 /api → :8000)
cd apps/web
npm install
npm run dev
```

打开浏览器 → `http://localhost:5173` → 选择术数专页 → 输生辰 → 排盘 → 收入合参 → `/heshen` 多法合参。

### Docker

```bash
docker compose up -d
# 后端 :8000 / 前端 :5173
```

---

## 项目结构

```
predict-life-and-all/
├── divination/                          # 核心排盘引擎包
│   ├── __init__.py                      # export Birth / ChartResult / compute / supported_methods
│   ├── contracts.py                     # Birth / ChartResult 数据契约
│   ├── router.py                        # 13 法 method → engine 字典 + 交叉验证/时辰校准/合盘
│   ├── meta.py                          # 方法元数据 (subject / mode / needs / recommended_for)
│   ├── astro_math.py                    # 西方占星数学层
│   ├── solartime.py                     # 真太阳时校正
│   ├── fengshui.py                      # 风水复合引擎
│   ├── engines/
│   │   ├── bazi.py          # lunar-python  八字四柱
│   │   ├── ziwei.py         # py-iztro      紫微斗数
│   │   ├── qimen.py         # 纯 Python 自实现 奇门遁甲
│   │   ├── western.py       # skyfield + 自算 西方占星
│   │   ├── vedic.py         # skyfield + Lahiri 吠陀占星
│   │   ├── liuyao.py        # 纯 Python 六爻
│   │   ├── meihua.py        # 纯 Python 梅花易数
│   │   ├── chenggu.py       # 称骨查表
│   │   ├── bazhai.py        # 八宅查表
│   │   ├── xuankong.py      # 玄空飞星 + 洛书
│   │   ├── tarot.py         # 塔罗 78 张完整牌阵
│   │   ├── numerology.py    # 毕达哥拉斯数字命理
│   │   ├── hepan.py         # 合盘 (多法双人)
│   │   ├── wuxing.py        # 五行通用工具
│   │   ├── yijing.py        # 易经卦象工具
│   │   └── engines_western_shared.py  # 西方引擎共享层
│   ├── interpret/                      # 解读编排
│   │   ├── prompts.py        # 系统提示 + 盘面序列化
│   │   ├── guardrails.py     # 危机/医疗/法律/财务转介
│   │   ├── client.py         # LLMClient / MockClient / AnthropicClient
│   │   └── reader.py         # 编排入口 + interpret_stream()
│   └── aggregation/                    # 多法聚合层
│       ├── schema.py         # ReadingRequest / ReadingResult / ReadingReport
│       ├── intent.py         # 意图分类器
│       ├── selector.py       # 术法选择 (三层权重)
│       ├── weights.py        # 各法权重配置
│       ├── normalizer.py     # 统一信号标准化 (28 SIGNAL_KEYS)
│       ├── validator.py      # 加权交叉验证 (consensus + conflicts)
│       ├── synthesizer.py    # 三档报告 (free/standard/premium)
│       ├── reading_service.py # 主编排服务
│       ├── safety.py         # 安全检查
│       └── llm_prompt.py     # LLM Prompt 构建器
│
├── server/                              # FastAPI HTTP 层
│   ├── main.py                          # FastAPI app (CORS + 日志 + 异常处理)
│   ├── api/
│   │   ├── methods.py     GET  /api/methods
│   │   ├── chart.py       POST /api/compute, /compute/multi, /calibrate/hour, /estimate/traits, /compatibility
│   │   ├── reading.py     POST /api/reading        (多法合参主入口)
│   │   ├── interpret.py   POST /api/interpret      (SSE 流式)
│   │   ├── daily.py       GET  /api/daily          (日签 + 塔罗 + 雷诺曼)
│   │   ├── almanac.py     GET  /api/almanac        (老黄历)
│   │   └── prompts.py     GET  /api/prompts/{method}
│
├── apps/web/                            # React + Vite 前端 (v2 一法一专页)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx                 # 首页 (14 法卡片 + 今日运势 + 排盘历史)
│   │   │   ├── methods/                 # ★ 一法一专页 (v2 闭环)
│   │   │   │   ├── BaziPage.tsx         # 八字 — 表单 → 四柱大字 → 五行雷达 → 大运
│   │   │   │   ├── ZiweiPage.tsx        # 紫微 — 12 宫盘面
│   │   │   │   ├── QimenPage.tsx        # 奇门 — 九宫格 + 问题
│   │   │   │   ├── LiuyaoPage.tsx       # 六爻 — 六爻竖排 + 本卦变卦
│   │   │   │   ├── MeihuaPage.tsx       # 梅花 — 主/互/变三卦
│   │   │   │   ├── ChengguPage.tsx      # 称骨 — 四柱重量 + 批语
│   │   │   │   ├── BazhaiPage.tsx       # 八宅 — 八方吉凶罗盘
│   │   │   │   ├── XuankongPage.tsx     # 玄空 — 飞星 3×3 格
│   │   │   │   ├── WesternPage.tsx      # 西方占星 — 行星 + 宫位
│   │   │   │   ├── VedicPage.tsx        # 吠陀 — Nakshatra
│   │   │   │   ├── TarotPage.tsx        # 塔罗 — 牌阵选择 + 牌面
│   │   │   │   └── NumerologyPage.tsx   # 数字命理
│   │   │   ├── HeShenPage.tsx           # ★ 合参卷宗 — 跨术数共识报告
│   │   │   ├── HePanPage.tsx            # 合盘 — 双人四维评级
│   │   │   ├── Reading.tsx              # 12 法全量合参
│   │   │   ├── Daily.tsx                # 今日个人化
│   │   │   ├── Almanac.tsx              # 老黄历
│   │   │   ├── Compatibility.tsx        # 合盘分析
│   │   │   ├── FengShui.tsx             # 风水综合
│   │   │   ├── Knowledge.tsx            # 知识馆
│   │   │   ├── History.tsx              # 排盘历史
│   │   │   ├── About.tsx                # 完整免责声明
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── Layout.tsx               # 导航 + 面包屑 + 页脚
│   │   │   ├── Sidebar.tsx              # 侧栏导航
│   │   │   ├── ElementsRadar.tsx        # 五行雷达图
│   │   │   ├── Jargon.tsx               # 术语悬浮提示
│   │   │   ├── ui.tsx                   # 纸墨 UI 公共组件
│   │   │   └── charts/                  # 14 个盘面可视化组件
│   │   ├── lib/
│   │   │   ├── types.ts                 # TS 类型 (含 Method / Birth / ChartResult / ReadingResult)
│   │   │   ├── api.ts                   # 后端 API 调用 (computeChart / fetchReading / fetchDaily)
│   │   │   ├── method-info.ts           # 方法说明文案
│   │   │   ├── share.ts                 # 方法标签映射
│   │   │   ├── cities.ts                # 全球城市经纬度预设
│   │   │   └── ...
│   │   └── store/
│   │       ├── birth.ts                 # Zustand: 全局生辰记忆 (localStorage persist)
│   │       ├── basket.ts                # Zustand: 合参卷宗 (localStorage persist)
│   │       ├── keys.ts                  # Zustand: LLM Key
│   │       └── ...
│   └── tailwind.config.js               # 纸墨设计 token
│
├── tests/
│   ├── test_api.py              # API 端点测试
│   ├── test_reading_service.py  # reading_service 测试
│   ├── test_safety.py           # 安全合规模块测试
│   ├── test_llm_prompt.py       # LLM Prompt 构建器测试
│   └── ...
│
├── docker-compose.yml
├── pyproject.toml
├── requirements_divination.txt
├── uv.lock
└── README.md
```

---

## 术数总览

| 类别 | 术数 | method id | 引擎 | 前端口 | 备注 |
|---|---|---|---|---|---|
| 东方·命 | 八字 | `bazi` | lunar-python | `/m/bazi` | 四柱 + 大运 + 五行强弱 |
| 东方·命 | 八字精算 | `bazi_v2` | lunar-python+shensha | — | 神煞 + 用神格局 + 职业适配 |
| 东方·命 | 紫微 | `ziwei` | py-iztro | `/m/ziwei` | 12 宫星曜 + 命身宫 + 限运 |
| 东方·卜 | 奇门遁甲 | `qimen` | 自实现 | `/m/qimen` | 九宫格 + 时家排盘 + 格局 |
| 东方·卜 | 六爻 | `liuyao` | 自实现 | `/m/liuyao` | 6 爻 + 世应 + 本卦变卦 |
| 东方·卜 | 梅花 | `meihua` | 自实现 | `/m/meihua` | 主/互/变三卦 + 体用生克 |
| 东方·命 | 称骨 | `chenggu` | 查表 | `/m/chenggu` | 四柱骨重 + 歌诀批语 |
| 东方·风 | 八宅 | `bazhai` | 查表 | `/m/bazhai` | 命卦 + 四吉四凶方 |
| 东方·风 | 玄空飞星 | `xuankong` | 洛书+飞星 | `/m/xuankong` | 三元九运 + 坐山向星 |
| 东方·合 | 合盘 | `hepan` | 多法自实现 | `/m/hepan` | 双人合盘 + 四维评级 |
| 西方 | 西方占星 | `western` | skyfield | `/m/western` | 本命盘 + 行星 + 相位 |
| 西方 | 吠陀占星 | `vedic` | skyfield+Lahiri | `/m/vedic` | 恒星黄道 + Nakshatra |
| 西方 | 塔罗 | `tarot` | 随机牌阵 | `/m/tarot` | 78 张 8 种牌阵 |
| 西方 | 数字命理 | `numerology` | 毕达哥拉斯 | `/m/numerology` | 生命灵数 + 大师数 |
| 东方·卜 | 大六壬 | `liuren` | 自实现 | — | 三式之首 (引擎就绪) |
| 东方·命 | 铁板神数 | `tieban` | 自实现 | — | 铁板条文 (引擎就绪) |
| 西方 | 雷诺曼 | `lenormand` | 随机 36 张 | — | Grand Tableau (引擎就绪) |
| 工具 | 时辰校准 | `hour_calibrator` | 12 时遍历 | — | 未知时辰定盘 |
| 验证 | 交叉验证 | `cross_validator` | 多法 ensemble | — | 多系统一致性检验 |

---

## API 契约

### `GET /api/methods`
返回全部术数的元数据 (id / school / group / subjects / modes / needs / recommended_for)。

### `POST /api/compute`
单法排盘 (method + birth + options{mode, spread, question, ...}) → ChartResult。

```json
// 请求
{ "method": "bazi", "birth": { "year": 1990, "month": 5, "day": 15, "hour": 8, ... }, "options": { "mode": "natal" } }

// 响应
{ "method": "bazi", "school": "east", "engine": "lunar-python",
  "normalized": { "elements": {"wood": 1.68, "fire": 0.5, ...}, "timeline": [...] },
  "raw": { "pillars": {...}, "day_master": "丁", "断": {...} },
  "elapsed_ms": 22 }
```

### `POST /api/compute/multi`
多法并行排盘 + 交叉验证 (methods[] + birth + subject) → charts + cross_validation。

### `POST /api/calibrate/hour`
时辰校准 — 12 时辰遍历评分 (birth + known_traits/career/events)。

### `POST /api/estimate/traits`
从性格特征反推出生时辰 (traits[])。

### `POST /api/compatibility`
双人合盘 (chart1_birth + chart2_birth + method/methods) → 兼容性打分。

### `GET /api/daily`
每日运势 (日柱干支 + 五行 + 塔罗牌 + 雷诺曼牌 + 个性化建议)。

### `GET /api/almanac`
老黄历 (农历日期 + 节气 + 宜忌)。

### `POST /api/reading` — 合参主入口
用户从卷宗提交已排盘面,多法加权验证,生成共识/冲突/建议/报告。

```json
// 请求
{ "question": "...", "birth": {...}, "methods": ["bazi","tarot",...], "depth": "standard", "language": "zh" }

// 响应
{ "consensus": [...], "conflicts": [...], "validation": { "confidence": 0.72, ... },
  "action_advice": [...], "risks": [...], "report": {...}, "disclaimer": "..." }
```

### `POST /api/interpret` (SSE 流式)
charts + question → NDJSON 流 (type: delta / done / error)。

### `GET /api/prompts/{method}`
每法系统提示模板。

**安全机制**: 危机词阻断 → 心理援助热线 / 敏感领域降级 / 绝对化软化 / 日志脱敏 / 名人案例已依法清除。

---

## 设计系统

**调性**: 宣纸墨色 — 古籍 × 仪器的克制神秘感。朱砂为唯一高饱和色点睛。避开塔罗摊俗气 (无紫色霓虹、无水晶球 emoji 堆砌)。

| Token | 色值 | 用途 |
|---|---|---|
| `--paper` | `#F4EFE6` | 宣纸底色 |
| `--paper-2` | `#EDE6D8` | 卡片/次级底色 |
| `--ink` | `#2B2620` | 墨色主文字 |
| `--ink-soft` | `#6B6256` | 次级文字 |
| `--cinnabar` | `#B03A2E` | 朱砂点缀 (唯一高饱和) |
| `--verdigris` | `#5A7058` | 铜绿辅助色 |
| `--rule` | `#C9BFA9` | 界格线 |
| `--indigo` | `#2F4858` | 法系标识 |

- 字体: 标题 `Cinzel` + `Noto Serif SC`, 正文 `Noto Serif SC`, 等宽 `JetBrains Mono`
- 盘面线条精细、留白充足、吉凶用色克制
- 移动端响应式 (窄屏盘面可横滚)
- 浅色优先 (宣纸),支持 class dark

---

## 合规与福祉

1. **免责声明常驻**: 每条解读底部附免责文案; `/about` 有完整版
2. **危机 block**: 命中"自杀/自残/轻生"等关键词时,只渲染心理援助转介,不出盘面与吉凶
3. **不放大焦虑**: UI 不用"大凶""死劫"等惊吓式标签; 凶用中性措辞 ("需留意""阻力")
4. **医疗/法律/财务**: 后端 `notes` 原样透传,不弱化
5. **不显示广告 / 不诱导成瘾式连续抽卦**
6. **用户 LLM Key 不落库**: 仅浏览器 localStorage; 后端不接收
7. **名人案例已依法清除**: 依《个人信息保护法》+《民法典》人格权编,删除所有真实人物出生数据

---

## 依赖 License 一览

| 库 | License | 作用 |
|---|---|---|
| lunar-python | MIT | 八字农历 |
| py-iztro | MIT | 紫微斗数 |
| skyfield | MIT | 西方星历 |
| JPL DE421 | 公有领域 | 行星位置 |
| FastAPI | MIT | HTTP |
| React / Vite / Tailwind | MIT | 前端 |
| Zustand | MIT | 状态管理 |

**全栈无 AGPL、无 SSPL、无 GPL。** 可放心闭源商用。

---

## 启动方式汇总

```bash
# ── 后端 ──
cd "E:\work\predict life and all"
python -m uvicorn server.main:app --reload --port 8000

# ── 前端 ──
cd apps/web
npm install
npm run dev                      # http://localhost:5173, 自动代理 /api → :8000

# ── TypeScript 检查 ──
cd apps/web && npx tsc --noEmit

# ── 测试 ──
cd "E:\work\predict life and all"
python -m pytest tests/ -v
```

---

## v0.3 — 前端重构 v2 (当前)

- ✅ **一法一专页** — 12 个 `/m/{method}` 页面,每法独立闭环 UX (表单 → 盘面 → 收入合参 → 重新排盘)
- ✅ **合参卷宗** — 用户主动将盘面收入 basket → `/heshen` 发起跨术数合参解读
- ✅ **全局生辰记忆** — Zustand birth store,跨页面同步,localStorage persist
- ✅ **宣纸墨色主题** — 品牌升级,朱砂点睛,古籍仪器质感
- ✅ **14 术数引擎** — 新增 hepan (合盘) / liuren (大六壬) / tieban (铁板神数) / lenormand (雷诺曼)
- ✅ **时辰校准 + 反向推算** — `/api/calibrate/hour` + `/api/estimate/traits`
- ✅ **每日运势 + 老黄历** — `/api/daily` + `/api/almanac`
- ✅ **双人合盘** — `/api/compatibility` 单法/多法加权评分
- ✅ **名人案例清除** — 依法删除 celebrity_cases.json (个人信息保护法 + 民法典人格权编)
- ✅ **TypeScript 严格模式** — 0 类型错误
- ✅ **安全增强** — 后端 interpret_stream() SSE 流式安全输出

## v0.2

- ✅ 12 法聚合解读 (`/api/reading`) — 统一调度、加权交叉验证、三档报告
- ✅ 安全合规模块 — 危机拦截、敏感领域降级、绝对化过滤、日志脱敏
- ✅ LLM Prompt 构建器 — 合规规则注入、Mock 模式、安全校验
- ✅ 报告历史 — localStorage 保存/重新打开/删除 (最多 50 条)

## 明确剔除 (不在范围)

- 用户系统 / 登录 / 支付 / 订阅 / Stripe
- 原生 App (只做 Web 响应式)
- 命理师市场 / 1v1 咨询 / 社交分享 / 邀请裂变
- 服务端 LLM Key 托管
- 命理准确性的科学论证

---

## License

Mystic Hub 自身采用 MIT License。
