# 下一步开发方案 v1.0（2026-06，6.21 事实校准）

> 基于「开发计划-古籍-优化-法器罗盘」整合精修版。
> **2026-06-21 校准**：本文件保留原方案结构，但已按当前代码事实修正过期 TODO；最新执行状态以 `README.md` 与 `docs/SESSION_2026-06-21.md` 为准。
> **范围**：A 开发计划（精确到文件级）· B 古籍推荐 + 版权规则 · C 优化清单 · D 法器与罗盘。
> **红线**：档位制（无单一分数）/ 无真人案例 / 公版原文入 RAG / 确定性随机 / 临界角双候选。

---

## 0. 工程现状与文档偏差（先看清）

| 项 | 文档说法 | 实际状态 | 处理 |
|----|----------|----------|------|
| Golden 测试 | 43 项 | golden 文件显式测试约 **47 项**；全量 `2146 passed` | ✅ 已超过 30+ 项门槛，后续继续补专业软件对照集 |
| `server/data/celebrity_cases.json` | 需下架 | 已不存在 | ✅ 已完成 |
| `uvicorn.log.err` | 需进 `.gitignore` | `.gitignore` 已有 `*.log`；文件还在工作树 | 一次性 rm，不入仓 |
| 评分档位制 | 改五档极性+计票 | `DimensionPolarity` / `SignalDigest` / `tally_by_scope` 已落地；业务代码无 `overall_score` 输出 | ✅ 已完成，保留测试注释作为迁移说明 |
| 古籍知识库 | 待建 | `divination/knowledge/{books,classical,domains,…}.py` 已成型 | RAG 入库语料与 cite 仍空 |
| 罗盘 API | 待建 | `server/api/compass.py` 已存在 | D1 三大坑（磁北/真北/临界角）未在前端落地 |
| 引擎数量 | 12 法 | 路由含 20 个 method key（`bazi`/`bazi_v2` 共享引擎，约 19 法） | 继续做主推/长尾分层，不再按“未落地”处理 |

---

## A. 开发计划（精确版 · 8–10 周）

**总纲**：先把"已验证但未合并"的成果塞进仓 + 把"档位制"红线落地，再做差异化（会审主线），最后扩面（流年/罗盘/古籍 RAG/新法）。

### Sprint 0（第 1 周）· 合并 + 红线（2026-06-21：主体已完成）

| # | 任务 | 改/加文件 | 验收判据（可命令化） |
|---|------|----------|--------------------|
| 0.1 | ✅ **删单一分数**：`DimensionPolarity` 五档枚举 `{strong_support / weak_support / neutral / weak_warn / strong_warn}` 已接入 | `divination/aggregation/schema.py`、`divination/aggregation/validator.py`、`divination/aggregation/synthesizer.py`、`tests/test_validator.py` | 业务代码无 `overall_score` 输出；测试保留迁移注释 |
| 0.2 | ✅ **计票制**：`tally_by_scope` 已落地，按 scope 输出支持/警示票数 | `divination/aggregation/scope_tally.py`、`validator.py`、`reading_service.py` | `tests/test_scope_tally.py` / `tests/test_validator.py` 覆盖 |
| 0.3 | ✅ **六爻深化**：纳甲六亲、六神、伏神/飞神、世应冲合已接入 | `divination/engines/liuyao.py` | `tests/test_liuyao_six_shen_fu_shen.py` 已解 skip，43 passed |
| 0.4 | **八字旺衰 + 藏干**：`wuxing.py` 加藏干表 + `element_strength` + `day_master_strength`；`bazi.py` 接入 + `zi_hour` 开关 | `divination/wuxing.py`、`divination/engines/bazi.py`、`tests/test_golden_classics.py` | 庚生巳月中和、三寅身强、子月众水从弱；23:30 双开关日柱不同 |
| 0.5 | ✅ **塔罗基础深化**：78 牌、9 阵、安全洗牌与承诺方案已完成；三系统融合仍另列 P3 | `divination/engines/tarot.py`、`divination/aggregation/method_inputs.py` | 78 张唯一 id；同 seed 同牌组；crypto 回归已入库 |
| 0.6 | ✅ **吠陀深化**：Rahu/Ketu、D9 Navamsa、庙旺、Vimshottari Dasha、Yogas 已接入 | `divination/engines/vedic.py`、`divination/data/vedic_yogas.py` | Makar Sankranti、Dasha=120、Yogas 表/引擎测试覆盖 |
| 0.7 | ✅ **黄金测试扩到 30+ 项**：当前 golden 文件显式测试约 47 项 | `tests/test_golden_*.py` | 全量 `python -m pytest tests/ -q` 已验证 2146 passed |
| 0.8 | **卫生**：`rm -f uvicorn.log uvicorn.log.err`；`*.log` 已在 `.gitignore`，确认无残留 | 工作树 | `git status` 不再列日志文件 |
| 0.9 | **奇门 golden 验证**：5 节气三元定局对照《烟波钓叟歌》 | `tests/test_golden_classics.py`（增） | 5 例皆过；不过即修排局算法 |
| 0.10 | **Linter 兜底**：禁 `Math.random()`、禁全局 `random.seed`、禁字符串 hardcode 二十四山 | 新增 `tools/lint_random.py` 或 ruff 自定义规则 | `make lint` 全绿；CI 必过门 |

**Sprint 0 验收门（必须全过）**：
1. `pytest tests/ -k golden` 全绿；
2. `grep -RIn "overall_score\|random\\.random\\(\\)" divination/` 返 0；
3. 报告样例中**无单一分数**，只有"几法支持/几法警示 + 分歧并陈"。

### Sprint 1–2（第 2–4 周）· 会审主线 Phase 1

按《会审平台-开发方案》落地：

| 子模块 | 文件 | 验收 |
|--------|------|------|
| 意图 FSM + LLM 兜底 | `divination/aggregation/intent.py`（扩） | 50 问例 F1 ≥ 0.9；低置信走 LLM 兜底并写回 |
| 追问（每类预设 1 问、最多 2） | `divination/aggregation/questioner.py`（新建） | 同一意图的追问确定性可重现 |
| 人事时地境限装配 | `divination/aggregation/situation.py`（新建） | 字段空缺即降级；不全为 None |
| `raw.断` → 五档 `SignalDigest` | `divination/aggregation/normalizer.py`、`method_inputs.py` | 五档枚举全覆盖；规则全部来自断法层，**LLM 不估** |
| 计票 + 分歧并陈 | `divination/aggregation/cross_validator.py`（Sprint 0 已建）+ `synthesizer.py` | 报告含「共识项 / 分歧项」两段 |
| 现实条件校正 | `divination/aggregation/reality.py`（扩） | 健康/法财自动转介；constraints 让命理结论降级（声明式规则表） |
| `cases`/`reading` API | `server/api/cases.py`（扩）、`server/api/reading.py`（改调度） | 创建/context/cast 幂等；result/versions 可回放；用户选定的方法集优先 |

**验收**：问"该不该接受这份工作" → 最小追问 → 一次固定会审报告，含分层共识/分歧、现实校正、可溯依据、**无单一分数**。

### Sprint 3（第 5 周）· 流年引擎 + 合盘分享卡（抓增长）

| 任务 | 文件 | 验收 |
|------|------|------|
| 八字流年/流月信号 | `divination/engines/bazi.py`（加 `liu_nian / liu_yue`） | 1984 甲子、1998 戊寅等节点对《滴天髓》 |
| 西占行运 transits | `divination/engines/western.py` + `engines_western_shared.py` | 次限/三限/行运分通道输出 |
| 紫微限运 | `divination/engines/ziwei.py` | 大限/流年/流月齐出 |
| 合盘分享卡 | `apps/web` 新增 `/share/hepan/[caseId]` 页 + `server/api/hepan_share.py` | 出可分享图（PNG/JPG）；OG meta；移动端可读 |

### Sprint 4（第 6–7 周）· 罗盘 + 空间（详见 D）

### Sprint 5（第 8 周）· 古籍 RAG 一期 + 追问式解读

- `divination/knowledge/classical.py` 接 `books.py` 推书 → 入 `divination/knowledge/corpus/`（公版原文 txt/jsonl）。
- 引用样式：`《书名·篇名》原文 + 自撰白话 + 出处 URL/影印版`。
- 解读追问：「这结论的依据是什么」→ 弹出原文片段 + 引用。

### Sprint 6（并行）· 新建 / 重排方法

| 方法 | 文件 | 优先级 |
|------|------|--------|
| 大六壬 | `divination/engines/liuren.py`（已建 181 行） | P0 验证 + golden |
| 小六壬 | `divination/engines/xiaoliuren.py`（已建 201 行） | P0 验证 + golden |
| 铁板神数 | `divination/engines/tieban.py` + `divination/data/tieban_verses.py` | ✅ 太玄数精校 / 纳音 / 分金 / 邵雍本与铁冠道人本双流派已接入 |
| 雷诺曼 | `divination/engines/lenormand.py`（已建） | P0 验证 + golden |

> 当前 method key 已多于「12 法」。后续重点不是补空壳，而是做「主推核心法 + 长尾法」的信息架构和入口分层。

**铁律**：Sprint 0 不全绿不进 Sprint 1；新引擎**先测试再实现**；档位制是绝对红线。

---

## B. 古籍推荐 + 版权规则

### B.0 使用规则（决定能不能用）

- ✅ **公版原典原文**：作者去世超期 / 宋明清古籍。可用、可入 RAG、可引出处。
- ❌ **现代点校 / 白话译注 / 评注本 / 译本**：有版权。古籍原文仍公版，但现代人的注释/白话/排版校勘是新作品。
- ❌ **英文译本**：译文多有版权，找公版译本或自译。
- ✅ 入库只存**原文**；现代解释由你方/专家自写（会审方案已定）。

### B.1 各法推荐书目

#### 八字
| 书 | 作者/年代 | 版权 | 用途 |
|----|----------|------|------|
| 渊海子平 | 宋·徐升 | ✅ 公版 | 古法格局派 |
| 三命通会 | 明·万民英 | ✅ 公版（四库本/哈佛藏本原文） | 格局/神煞/纳音集大成 |
| 滴天髓 · 阐微 | 传宋·京图 / 明·刘基注 / 清·任铁樵 | ✅ 公版 | 旺衰派 |
| 子平真诠 | 清·沈孝瞻 | ✅ 公版（徐乐吾评注 1948 殁，已逾保护期） | 用神成败 |
| 穷通宝鉴 | 清·余春台 | ✅ 公版 | 调候用神（旺衰升级直接引） |
| 神峰通考 | 明·张楠 | ✅ 公版 | 病药/盖头 |

#### 紫微
| 书 | 版权 | 用途 |
|----|------|------|
| 紫微斗数全书（明刊本） | ✅ 公版 | 排盘/星情 |
| 紫微斗数全集（明刊） | ✅ 公版 | 补充 |
> ⚠️ 中州派（王亭之）等现代流派著作有版权，不入库。

#### 奇门
| 书 | 版权 | 用途 |
|----|------|------|
| 烟波钓叟歌 | ✅ 公版 | 定局/格局总诀（已 golden 验） |
| 奇门遁甲统宗 / 御定奇门宝鉴 | ✅ 公版 | 干组合格局 |

#### 六爻
| 书 | 版权 |
|----|------|
| 周易（古经+十翼） | ✅ |
| 京氏易传（汉·京房） | ✅ 纳甲/八宫（已用） |
| 增删卜易（清·野鹤老人） | ✅ 用神取用（已用） |
| 卜筮正宗（清·王洪绪） | ✅ |
| 易隐 · 易冒（清） | ✅ |

#### 梅花 / 风水 / 玄空 / 八宅 / 罗盘 / 称骨
- 梅花易数（宋·邵雍）✅
- 葬书（晋·郭璞）✅、青囊经/奥语/天玉经（传唐·杨筠松）✅、撼龙/疑龙经（唐·杨筠松）✅
- 地理辨正（清·蒋大鸿）✅、沈氏玄空学（民国·沈竹礽 1849–1906）✅（已用）
- 八宅明镜（清·箬冠道人）✅、阳宅三要（清·赵九峰）✅
- 罗经透解（清·王道亨）✅
- 称骨歌（传唐·袁天罡）✅

#### 大六壬 / 小六壬
- 六壬大全（明）✅、大六壬指南（清·程爱村）✅、六壬神课金口诀 ✅、诸葛马前课/小六壬掌诀 ✅

#### 铁板神数 ⚠️
- 原典传抄 ✅，但**条文/考刻表多为现代秘传或商业重构**（常有版权或不公开）。
- 当前已做太玄数编码、纳音/分金、考刻分与双流派条文范围回归；后续新增条文仍必须确认合法来源。

#### 西占
- Tetrabiblos（托勒密 2c）✅ 原文；公版英译（Loeb / Ashmand 1822）
- Christian Astrology（Lilly, 1647）✅
- Alan Leo（1860–1917）✅
> ⚠️ Robert Hand、Liz Greene 当代著作有版权。

#### 吠陀
- Brihat Parashara Hora Shastra ✅ 原文；英译多版权 → 公版译本或自译
- Brihat Jataka（Varahamihira 6c）✅、Phaladeepika / Saravali（中世纪）✅

#### 塔罗 / 雷诺曼 / 数字命理
- Pictorial Key to the Tarot（Waite 1910）✅、RWS 牌图（Smith 1909）✅
- Petit Lenormand 36 牌义（19c）✅
- 毕达哥拉斯体系 ✅ 公共知识；具体释义文字须自撰

### B.2 入库 schema（建议）

```json
{"id":"bazi-yuanhai-001","book":"渊海子平","chapter":"...",
 "dynasty":"宋","author":"徐升","copyright":"public_domain",
 "source":"四库全书子部/哈佛燕京藏本",
 "text":"...原文片段≤500字...",
 "tags":["格局","正官","七杀"]}
```

### B.3 索引与检索
- 简易方案：`divination/knowledge/corpus/{bazi,ziwei,...}.jsonl`，启动时建内存倒排（够用）。
- 进阶方案：faiss / sqlite-vec（后期）。

---

## C. 优化清单

### C1 准度
| 法 | 补什么 | 文件 |
|----|--------|------|
| 八字 | 通根远近/虚透、神煞表（天乙/桃花/驿马/华盖/羊刃）、扶抑+调候并陈 | `divination/wuxing.py`、`divination/engines/bazi.py` |
| 六爻 | 伏神（用神不上卦装本宫首卦伏神）、六合六冲、用神两现、进退神 | `divination/engines/liuyao.py` |
| 奇门 | 干组合格局（青龙返首/飞鸟跌穴…，每条带《统宗》书证） | `divination/engines/qimen.py` |
| 玄空 | 兼向替卦（兼线 3° 内启用替星） | `divination/engines/xuankong.py` |
| 紫微 | 四化（化禄权科忌）入断 | `divination/engines/ziwei.py` |
| 西占 | 三王星+月交点、150°/45° 相位、容许度按行星分级 | `divination/engines/western.py` |
| 称骨 | 印本校订 51 档批语 | `divination/engines/shicao.py` |
| ⚠️ | "专业软件对照集"：每法 10–20 例对公认排盘工具，固化进 CI | `tests/test_golden_classics.py` |

### C2 工程
- **禁 `random.random()`**（lint 扫描），统一 `RandomService(seed_hash + algo_version)`；
- 依赖锁版本（`uv.lock` 已用），任何升级 golden 全绿才并入；
- 排盘缓存（同盘同问幂等，省 LLM）；
- 星历 `de421.bsp` 已 `*.bsp` 排除 → **打进镜像**，禁运行时下载。

### C3 性能 / 体验
- 会审并行排盘（多法并发）；
- 解读 SSE 流式（已有）+ 按句出现的书写节奏；
- 盘面 SVG 懒加载；移动端窄屏盘面横滚/缩放。

### C4 合规
- 名人案例零残留（已 ✅）；
- 广告与敏感结论/风险提醒严格隔离；
- 出海部署 + GDPR 最小合规（数据删除自助、盘面去标识进 LLM、隐私政策）。

---

## D. 法器与罗盘模块

### D1 罗盘（空间数据采集，非第 N 法）

**三通道输入**：手机罗盘 / 实体罗盘录入 / 手动角度 / 地图方向。

**⚠️ 必解决的三个技术坑（不解决会系统性偏角）**：

1. **磁北 vs 真北**
   - `DeviceOrientationEvent.alpha` 在 iOS/Android 不同给的是磁北或真北不一；**风水罗盘传统用磁北**。
   - 必做：明确 `north_ref` 是 `magnetic` 或 `true`；如需统一按经纬度用 NOAA/WMM 磁偏角校正；让用户知道用的是哪种北（流派有别）。

2. **iOS 权限**：`DeviceOrientationEvent.requestPermission()` 须**用户手势触发**（点击"开始测量"按钮）。

3. **校准与抖动**：连续采样 ≥30 次 → 均值 + 标准差；波动大提示远离金属/电器复测。

**红线**（沿用平面图方案）：
> 距二十四山山界 < 5° → 返回 **双候选 + 建议复测**，绝不静默择一。

**数据模型**：
```json
{"heading":187.4,"north_ref":"magnetic","declination_applied":-6.2,
 "mountain":"午","measurement_point":"入户门","sample_count":30,
 "deviation":4.2,"confidence":"medium","dual_candidate":null}
```

**接入**：八宅 / 玄空 / 风水形势 + 八字喜忌辅助；户型图按扇区法归宫（详见《开发方案-化解层与风水平面图》）。

**落地文件**：`apps/web` 新增 `/compass` 页（采样 + 校准 UI）、`server/api/compass.py` 已存在需扩 + `divination/engines/bazhai.py / xuankong.py / fengshui.py` 接入。

### D2 测算器具（A 类 · 参与测算）

| 工具 | 关键实现 | 文件 |
|------|---------|------|
| 三枚铜钱 | 存**六次原始投掷**（不直接选卦），接 `RandomService` | `divination/engines/liuyao.py` |
| 蓍草 | 揲蓍模拟 + 过程展示。**真概率**：老阳 9=3/16、少阳 7=5/16、少阴 8=7/16、老阴 6=1/16（≠ 铜钱）；golden 验四象分布 | `divination/engines/liuyao.py`（mode=shicao） |
| 塔罗 / 雷诺曼 | Fisher-Yates + 独立正逆；实体录入只解释 | `divination/engines/{tarot,lenormand}.py` |
| 罗盘 | 见 D1 | — |
| 签筒 | 绑具体签谱抽签，签谱须公版/自有 | `divination/engines/xiaoliuren.py` 或新增 `qian.py` |
| 鲁班尺 | 空间尺寸录入，红/黑字吉凶段查表 | `divination/engines/fengshui.py`（扩） |
| 数字 / 骰子 | 安全随机 | `divination/engines/numerology.py` |

### D3 仪式法器（B 类 · 不参与评分 → 资料库）

令牌 / 法印 / 法铃 / 法剑 / 香炉 / 金刚杵 / 念珠 → 传统器物资料库：

```json
{"name":"令牌","tradition":"道教","origin":"...",
 "usage":"使用场合","form":"文物形制","regional_variants":"地区流派差异",
 "digitizable":true,"sources":["公版文献/博物馆公开资料"]}
```

> ⚠️ 只做文化资料；不进测算评分。

### D4 民俗物品（C 类）

水晶 / 葫芦 / 五帝钱 → 只做文化资料或普通空间建议（接化解层 free/low 档）。

**红线**：
- 不承诺改命 / 消灾 / 治病 / 招财；
- 不恐吓、不带高价货；
- 表述限于"传统习俗 / 文化含义 / 空间布置参考"。

---

## 风险与红线总览

| 风险 | 红线 | 兜底 |
|------|------|------|
| 单一分数诱导用户 | 报告无 `overall_score` | 五档极性 + 计票 |
| 真人案例侵权 | 全站零真人案例 | 用虚构示例盘替代 |
| 版权古籍 | 只入公版原典原文 | 入库 schema 必填 `copyright` 字段 |
| 随机不可复现 | 禁 `random.random()` | `RandomService(seed_hash + algo_version)` |
| 空间系统性偏角 | 罗盘临界角必须双候选 | 距山界 < 5° → 双候选 + 复测 |
| 铁板条文版权 | 新增条文须有合法来源 | 现有条文库保留来源说明与回归测试 |

---

## 一句话收束

**顺序就是价值**：
1. 已完成项不再回炉：五档制、golden 扩容、六神、铁板、塔罗安全抽牌、奇门阴阳遁等按现状维护。
2. 继续推进还没产品化的差异项：观音/关帝灵签完整入口、古籍 RAG 与文献出处面板。
3. 主推/长尾分层要服务上架和维护，不再以“12 法是否凑齐”为目标。
4. 新增资料必须先解决版权与来源，再进入 engine/API/frontend。

规划已经够多，现在是**精确落地**的阶段。
