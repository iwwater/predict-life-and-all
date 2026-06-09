# Mystic Hub

> 中西融通玄学排盘 + AI 解读 Web App  
> 12 种术数统一接口 / 纯 MIT+BSD / 零 AGPL / 可闭源商用

8 个 GitHub 仓库 + 1 份 `divination/` 排盘引擎骨架融合而成的单体 Super App:

- **后端**: FastAPI 单体,核心引擎层即 `divination/` 骨架(`lunar-python` + `py-iztro` + 自实现奇门 + `skyfield` + 自算西方数学)
- **前端**: React 18 + Vite 5 + TypeScript + Tailwind 3,响应式 Web
- **AI 解读**: 用户在前端自备 OpenAI / Claude / Gemini / DeepSeek Key,后端只暴露 Prompt 模板
- **覆盖**: 12 大占卜法 —— 八字、紫微、奇门、六爻、梅花、称骨、八宅、玄空飞星、西方占星、吠陀占星、塔罗、数字命理

> 免责声明:本平台为传统文化与自我反思工具,所有解读**非科学预测**,不构成医疗 / 法律 / 财务 / 投资建议。涉及健康、法律、投资的决定请咨询专业人士。

---

## 快速开始

### 方式一:本地直跑(开发用)

```bash
# 1) Python 后端(uv 推荐,venv 也行)
uv sync                                          # 安装所有 Python 依赖
uv run python -m divination.test_run             # 跑 12 法冒烟测试

# 2) 启动后端(端口 8000)
uv run uvicorn server.main:app --reload --port 8000

# 3) 启动前端(端口 5173)
cd apps/web
npm install
npm run dev                                      # 默认 http://localhost:5173
```

打开浏览器 → 设置里填 LLM Key → 选一个或多个占卜 tab → 输生日 → 看排盘 + AI 解读。

### 方式二:Docker 一键起

```bash
docker compose up -d
# 后端:  http://localhost:8000
# 前端:  http://localhost:5173
docker compose logs -f        # 查日志
docker compose down           # 停
```

---

## 项目结构

```
predict-life-and-all/
├── divination/                          # 核心排盘引擎包(纯 Python,无网络)
│   ├── __init__.py                      # export Birth / ChartResult / compute / compute_all
│   ├── contracts.py                     # Birth / ChartResult 数据契约
│   ├── router.py                        # 12 法 method → engine 字典
│   ├── astro_math.py                    # 西方占星数学层
│   ├── test_run.py                      # 端到端冒烟测试
│   ├── engines/
│   │   ├── bazi.py          # lunar-python
│   │   ├── ziwei.py         # py-iztro
│   │   ├── qimen.py         # 纯 Python 自实现(无 AGPL 依赖)
│   │   ├── western.py       # skyfield + 自算
│   │   ├── vedic.py         # skyfield + Lahiri ayanamsa
│   │   ├── liuyao.py        # 纯 Python,基于 hash 复现
│   │   ├── meihua.py        # 纯 Python,基于时辰起卦
│   │   ├── chenggu.py       # 称骨查表
│   │   ├── bazhai.py        # 八宅查表
│   │   ├── xuankong.py      # 玄空飞星 + 洛书
│   │   ├── tarot.py         # 塔罗牌阵(随机 + 占位解)
│   │   └── numerology.py    # 毕达哥拉斯数字命理
│   └── interpret/                      # 解读编排
│       ├── prompts.py        # 12 法系统提示 + 盘面序列化
│       ├── guardrails.py     # 危机/医疗/法律/财务转介 + 绝对化软化
│       ├── client.py         # LLMClient 抽象 + MockClient + AnthropicClient
│       └── reader.py         # 编排入口
│
├── server/                              # FastAPI HTTP 层
│   ├── main.py                          # FastAPI app
│   ├── api/                             # 5 个端点
│   │   ├── methods.py     GET  /api/methods
│   │   ├── chart.py       POST /api/compute
│   │   ├── interpret.py   POST /api/interpret      (SSE 流式 NDJSON)
│   │   ├── prompts.py     GET  /api/prompts/{method}
│   │   └── cases.py       GET  /api/cases
│   ├── llm/prompts/                    # 5 类系统提示模板
│   │   ├── bazi.md / ziwei.md / qimen.md / western.md / vedic.md / combined.md
│   └── data/celebrity_cases.json       # 8 个名人案例(从 life-kline 搬来)
│
├── apps/web/                            # React + Vite 前端
│   ├── src/
│   │   ├── pages/                       # 6 个页面
│   │   │   ├── Home.tsx                 # 首页(12 法分类卡片)
│   │   │   ├── Cast.tsx                 # 排盘入口(出生信息 + 12 法多选 + 各法额外参数)
│   │   │   ├── Result.tsx               # 结果页(盘面 Tab + 流式解读面板)
│   │   │   ├── MethodInfo.tsx           # 单法说明
│   │   │   ├── History.tsx              # 本地历史
│   │   │   └── About.tsx                # 完整免责声明
│   │   ├── components/
│   │   │   ├── Layout.tsx               # 导航/页脚
│   │   │   ├── Settings.tsx             # LLM Key 管理(浏览器本地)
│   │   │   ├── Interpretation.tsx       # 流式解读面板
│   │   │   ├── BaziKline.tsx            # 八字 K 线 canvas
│   │   │   ├── ElementsRadar.tsx        # 5 元素雷达
│   │   │   ├── ui.tsx                   # 公共 UI(SchoolChip / EmptyBox / SkeletonBlock)
│   │   │   └── charts/                  # 12 个盘面 SVG 组件 + ChartRenderer
│   │   ├── lib/
│   │   │   ├── types.ts                 # ChartResult TS 类型
│   │   │   ├── api.ts                   # 后端调用 + SSE 解析
│   │   │   ├── llm-client.ts            # 浏览器直连 OpenAI/Claude/Gemini/DeepSeek
│   │   │   ├── kline.ts                 # K 线绘制算法
│   │   │   └── markdown.ts              # 解读文本渲染
│   │   └── store/
│   │       ├── keys.ts                  # Zustand:LLM Key
│   │       └── history.ts               # Zustand:历史(localStorage persist)
│   └── tailwind.config.js               # 设计 token(语义化色板)
│
├── tests/
│   └── test_api.py                      # 端到端冒烟:12 法 + 解读 + 危机 block
│
├── docker-compose.yml
├── Dockerfile.server
├── Dockerfile.web
├── .dockerignore
├── pyproject.toml
└── README.md
```

---

## 12 种术数

| 类别 | 术数 | method id | 引擎 | 备注 |
|---|---|---|---|---|
| 东方·命 | 八字 | `bazi` | lunar-python | 四柱 + 大运 + 五行强弱 |
| 东方·命 | 紫微 | `ziwei` | py-iztro | 12 宫方形盘 + 命主/身主 |
| 东方·卜 | 奇门遁甲 | `qimen` | 自实现 | 九宫格 + 真太阳时 + 格局/空亡 |
| 东方·卜 | 六爻 | `liuyao` | 自实现(hash 复现) | 6 爻竖排 + 本卦/变卦 |
| 东方·卜 | 梅花 | `meihua` | 自实现(时辰起卦) | 主/互/变三卦 + 体用 |
| 东方·卜 | 称骨 | `chenggu` | 查表 | 年月日时骨重 + 批语 |
| 东方·风 | 八宅 | `bazhai` | 查表 | 八方罗盘 + 游年星 |
| 东方·风 | 玄空飞星 | `xuankong` | 洛书 + 飞星 | 运/山/向 + 格局 |
| 西方 | 占星 | `western` | skyfield + 自算 | 圆形星盘 + 行星 + 相位线 |
| 西方 | 吠陀 | `vedic` | skyfield + Lahiri | 北印度方形盘 + Nakshatra |
| 西方 | 塔罗 | `tarot` | 随机 | single/three/celtic 牌阵 |
| 西方 | 数字命理 | `numerology` | 毕达哥拉斯 | 生命灵数 + 命运数 |

---

## API 契约

### `GET /api/methods`

返回 12 个方法的元数据,前端按此动态渲染多选框与各法额外参数表单:

```json
[
  {"id":"bazi","name":"八字","school":"east","group":"命","needs":["birth"]},
  {"id":"xuankong","name":"玄空飞星","school":"east","group":"风水","needs":["period","sitting"]},
  {"id":"tarot","name":"塔罗","school":"west","group":"西方","needs":["spread","question"]},
  ...
]
```

### `POST /api/compute`

```json
// 请求
{
  "method": "bazi",
  "birth": {
    "year": 1990, "month": 5, "day": 15, "hour": 8, "minute": 30,
    "gender": "male", "calendar": "gregorian",
    "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai",
    "is_leap_month": false
  },
  "options": { "period": 9, "sitting": "子", "spread": "three", "seed": null, "query": "事业" }
}

// 响应 = ChartResult
{
  "method": "bazi", "school": "east", "engine": "lunar-python",
  "normalized": {
    "elements": {"metal": 3, "wood": 1, "water": 2, "fire": 0, "earth": 2},
    "timeline": [
      {"from": "2000-01-01", "to": "2009-12-31", "label": "戊辰", "score": null}
    ]
  },
  "raw": { "pillars": {...}, "day_master": "木", "断": {...} }
}
```

### `POST /api/interpret`(流式,NDJSON)

```json
// 请求
{ "charts": [<ChartResult>, ...], "question": "今年事业如何?", "client": "mock" }

// 响应:SSE 流,每行一个 JSON
{"type":"delta","text":"【整体】..."}
{"type":"delta","text":"..."}
{"type":"done","meta":{
  "blocked": false, "softened_terms": ["注定"],
  "methods": ["bazi","western"], "flags": []
}}
```

**`blocked=true` 时**(危机话题命中):只返回一条转介文案,不出解读,前端不渲染任何盘面吉凶。

### `GET /api/prompts/{method}` `GET /api/cases`

查看每法的系统提示模板,以及 8 个名人排盘示例。

---

## 设计系统

**调性**:克制的神秘感 + 专业可信。避开塔罗摊俗气(无紫色霓虹、无水晶球 emoji 堆砌)。参考"天文馆 / 高端命理顾问"的质感。

| Token | 色值 | 用途 |
|---|---|---|
| `--bg` | `#0E1117` | 近黑夜空蓝,主背景 |
| `--surface` | `#161B22` | 卡片/容器 |
| `--ink` | `#E6E1D3` | 暖白文字 |
| `--muted` | `#8A8F98` | 次级文字 |
| `--gold` | `#C9A24B` | 主点缀:星图金 |
| `--jade` | `#4FB3A0` | 东方·青(命/卜/风) |
| `--azure` | `#5B8DEF` | 西方·蓝(占星/吠陀/塔罗/数字) |
| `--danger` | `#C8553D` | 凶/警示 |
| `--ok` | `#5AA469` | 吉 |

- 字体:标题思源宋体(`Noto Serif SC`),正文无衬线(`Inter` / 思源黑体)
- 盘面线条精细、留白充足、吉凶用色克制
- 移动端响应式(窄屏盘面可横滚)
- 全站深色优先

---

## 合规与福祉

1. **免责声明常驻**:每条解读底部附后端返回的免责文案;`/about` 有完整版
2. **危机 block**:命中"自杀/自残/轻生/不想活/活不下去/想死"时,只渲染转介文案,不出盘面与吉凶
3. **不放大焦虑**:UI 不用"大凶""死劫"等惊吓式标签;凶用中性措辞("需留意""阻力")
4. **医疗/法律/财务**:后端 `notes` 原样透传,不弱化
5. **不显示广告 / 不诱导成瘾式连续抽卦**
6. **用户 LLM Key 不落库**:仅浏览器 localStorage;后端不接收

---

## License 一览(已逐项核)

| 库 | License | 作用 |
|---|---|---|
| lunar-python | MIT | 八字 |
| py-iztro | MIT | 紫微 |
| skyfield | MIT | 西方星历 |
| JPL DE421 | 公有领域 | 行星位置 |
| FastAPI | MIT | HTTP |
| React / Vite / Tailwind | MIT | 前端 |
| Zustand / marked | MIT | 状态 / Markdown |

**全栈无 AGPL、无 SSPL、无 GPL。** 可放心闭源商用。

**自实现**绕开:`kinqimen`(自写奇门)、`iztro-py`(用 py-iztro)、`BaziEval C++`(lunar-python 足够)。

---

## 启动方式汇总

```bash
# 后端
.\.venv\Scripts\python.exe -m uvicorn server.main:app --port 8000

# 前端
cd apps/web && npm run dev      # http://127.0.0.1:5173,自动代理 /api → :8000

# 端到端测试
.\.venv\Scripts\python.exe tests\test_api.py
# 或 pytest
.\.venv\Scripts\python.exe -m pytest tests/test_api.py -v -s
```

---

## v0.1 不在范围(明确剔除)

- 用户系统 / 登录 / 支付 / 订阅 / Stripe
- 原生 App(只做 Web 响应式)
- 命理师市场 / 1v1 咨询 / 社交分享 / 邀请裂变
- 服务端 LLM Key 托管
- Placidus 宫位、塔罗之外更多牌阵
- 多语言 i18n(中英先做)
- 命理准确性的科学论证

---

## License

Mystic Hub 自身采用 MIT License。
