# 跨验证对照：本项目 vs dzcmemory-web/bazi-ziwei-skill

> 本项目参考了对标项目 `dzcmemory-web/bazi-ziwei-skill` (TS + HTML, MIT, 311 stars)
> 的核心架构思想。本文档对比两套实现的异同、优劣、以及本项目的差异化优势。

---

## 1. 总览对比

| 维度 | dzcmemory-web/bazi-ziwei-skill | 本项目 (mystic-hub) |
|---|---|---|
| **类型** | Agent Skill (SKILL.md) | 完整应用 (前端 + 后端 + 数据库) |
| **主语言** | TypeScript (72.2%) + HTML (27.8%) | Python (引擎) + TypeScript (前端) |
| **核心算法** | 八字 + 紫微斗数 | **18 种术法** (中西合参) |
| **License** | MIT | MIT |
| **跨验证** | Bazi×Ziwei 双向 | **多术法加权集成** (Bazi×Ziwei×Western×Vedic×...) |
| **渲染** | 单 HTML 海报 | 完整 React UI + 多专页 |
| **古文献** | 无（仅算法 + prompts）| **60 本古籍 + 83 条规则 + 68 RAG 文件** |
| **测试** | 4 例样本 | **1097 项 pytest** + TypeScript 检查 |

---

## 2. 三大核心原则对照

### dzcmemory-web 的三大原则（来自 README）
1. **LLM 只做分析** — 排盘/渲染不由 LLM 负责
2. **算法 → 文本 → LLM → 模板渲染** — 三阶段流水线
3. **分离关注点** — 算法/文本/渲染各自独立

### 本项目的对应实现
1. **算法层** (`divination/engines/`) — 自实现 + py-iztro + skyfield 等库, **确定性算法**
2. **结构化输出** (`divination/contracts.py` ChartResult) — 标准化数据结构
3. **LLM 解读层** (`divination/interpret/`) — 护栏 + LLM 输出 + 二次护栏
4. **前端渲染** (`apps/web/`) — React + paper-墨色主题, 多专页

✅ **本项目完整覆盖 dzcmemory-web 的三大原则**，且额外加了护栏层（guardrails）。

---

## 3. 跨验证（Cross-Validation）核心对比

### dzcmemory-web 的跨验证（Bazi × Ziwei）

来自 `prompts/zonghe-yinzheng-prompt.md` 的设计：

| 对齐维度 | 描述 |
|---|---|
| **主轴对齐** | 两系统的核心判断一致（如性格主调、事业方向）|
| **人生窗口对齐** | 关键年份（如事业高峰、婚姻时点）一致 |
| **冲突解决** | 当两系统不一致时,优先信任更具体/可验证的那个 |

### 本项目的跨验证 (`divination/engines/cross_validator.py`)

```
多术法独立计算 → 特征提取 → 加权集成 → 协议矩阵 → 综合评估
```

**核心创新**：
1. **多维度权重表** (`SYSTEM_DOMAIN_WEIGHTS`):
   - 八字擅命/财/大运（0.75-0.85）
   - 紫微擅关系/疾厄（0.75-0.80）
   - 西占擅关系/心理（0.80）
   - 奇门擅决策/失物（0.85-0.90）
   - 按域差异化加权，而非一视同仁

2. **协议矩阵** (`agreement_matrix`):
   - 每个域（self_life / career / wealth / relationship / health / annual_luck）
   - 每术法在该域的协议度
   - 输出 0-1 的置信度分数

3. **冲突解决** (`_resolve_conflict`):
   - 置信度高的优先
   - 多系统一致 → 高置信
   - 系统分歧 → 暴露不确定性（不强制结论）

4. **领域检查** (`domain_checks`):
   - 7 大领域独立检查（事业/财富/关系/健康/性格/流年/六亲）
   - 每个领域可独立触发深度分析

---

## 4. 算法层对比

| 术法 | dzcmemory-web | 本项目 |
|---|---|---|
| 八字排盘 | 借用 Yiqi (MIT) | lunar-python + 自实现 |
| 紫微排盘 | 借用 Yiqi | py-iztro |
| 大运/流年 | Yiqi 内置 | 自实现（含节气校正、真太阳时、夏令时）|
| 旺衰判断 | Yiqi 算法 | 自实现（藏干计权 + 月令系数 + 三因子）|
| 调候 | 简化 | 穷通宝鉴 调候用神完整表 |
| 神煞 | Yiqi 内置 | 自实现（含天乙贵人、文昌、驿马、桃花、羊刃 等）|
| 西方占星 | ❌ | ✅（含三通道：行运/次限/太阳返照）|
| 印度吠陀 | ❌ | ✅（含 Lahiri ayanamsa + Vimshottari Dasha）|
| 数字命理 | ❌ | ✅（毕达哥拉斯 + 中文三才五格）|
| 大六壬 | ❌ | ✅（720 课 + 59 课体 + 30 神煞）|
| 铁板神数 | ❌ | ✅（177 条 + 13 类 + 考刻分）|

✅ **本项目覆盖更广**，且中文核心（八字/紫微/六壬/铁板）的实现 **深度自研**，不依赖单一外部包。

---

## 5. 古籍依据对比

### dzcmemory-web
- **无** 古典文献条目
- 知识全部编码在 prompts（`prompts/*.md`）
- 算法 + prompts 是仅有的"知识来源"

### 本项目
- **60 本古籍**（`divination/knowledge/books.py` BOOK_CATALOG）
- **83 条结构化规则**（`divination/knowledge/classical.py` CLASSICAL_RULES）
- **68 个 RAG 参考文件**（`server/llm/references/`）
- **古今对应**: 每条规则有 `source` (出处) + `passage` (原文) + `confidence` (置信度)

✅ **本项目有完整的古籍溯源能力**——这是对标项目所欠缺的。

---

## 6. LLM Prompt 设计对比

### dzcmemory-web 的 prompt 架构
```
calculator/ → chart.json (deterministic)
       ↓
prompt: bazi-prompt.md / ziwei-prompt.md / zonghe-yinzheng-prompt.md
       ↓
LLM: analysis.json (long-form text)
       ↓
template: report-zonghe-poster.html → 海报
```

### 本项目的 prompt 架构
```
engines/ → ChartResult (standardized)
       ↓
classical_rules + RAG references
       ↓
prompt: aggregation/synthesizer.py → structured context
       ↓
guardrails: crisis_referral / medical_redir / hedging / disclaimer
       ↓
LLM (pluggable: Claude/GPT/etc.)
       ↓
post-guardrails: 二次护栏 + 免责声明注入
       ↓
frontend: ReadingReportView
```

✅ **本项目多了三层护栏**（guardrails），更符合医疗/法律级别的安全要求。

---

## 7. 测试覆盖对比

### dzcmemory-web
- 仅 4 例合成命主样本（明确标注"合成非真人"）
- 无自动化测试套件

### 本项目
- **1097 项 pytest 测试**（核心算法 + 古籍规则 + 排盘边界）
- TypeScript 编译零错
- 黄金测试用例（`test_golden_expanded.py`）
- 已验证案例数（books.py 中 `verified_examples`）

✅ **本项目测试覆盖度高 270 倍**，适合生产级部署。

---

## 8. 部署方式对比

### dzcmemory-web
- 单 HTML 海报（一次性输出）
- CLI 工具（Node.js）
- 适合 Agent 调用（Claude Code / Cursor / Codex）

### 本项目
- 完整 FastAPI 后端（30+ 端点）
- React 前端（30+ 页面）
- Cloudflare Pages Functions API 代理
- Docker 容器化
- 可独立部署的 SaaS 应用

✅ **本项目可直接面向终端用户**（非 Agent-only）。

---

## 9. 借鉴要点

本项目从 dzcmemory-web 借鉴的关键思想：

| 借鉴点 | 落地位置 |
|---|---|
| 三大原则（算法/分析/渲染分离）| 全部 19 个 engines 模块严格遵循 |
| 跨验证三维度（主轴/窗口/冲突）| `cross_validator.py` `_resolve_conflict()` |
| 确定性算法优先 | 引擎层零 LLM 调用，全部数学/规则推导 |
| 静态分析 + 海报模板 | `interpretation/reader.py` 输出 Markdown + HTML |

---

## 10. 差异化优势（本项目独占）

| 优势 | 体现 |
|---|---|
| **古籍溯源** | 60 本古籍 + 83 条规则 + 68 RAG 文件 |
| **18 术法全覆盖** | 中西合参，远超 2 术法对标 |
| **720 课大六壬** | 完整九宗门 + 课体 + 神煞 |
| **铁板神数考刻分** | 父母生肖校验机制 |
| **测试覆盖率 270x** | 1097 项 pytest |
| **生产级部署** | Docker + Cloudflare Pages |
| **护栏层** | 三层 safety guardrails |
| **RAG 注入** | 古籍自动结构化注入 LLM prompt |
| **前端文献面板** | 17 专页可折叠文献出处 |

---

## 11. 后续可互相借鉴的方向

| 借鉴方向 | 难度 | 价值 |
|---|---|---|
| dzcmemory-web 的 SKILL.md 标准化 → 本项目 Claude Code Skill 化 | 中 | 高 |
| dzcmemory-web 的 HTML 海报模板 → 本项目 React 海报组件 | 低 | 中 |
| dzcmemory-web 的样本命例 → 本项目 Golden 测试扩展 | 低 | 高 |
| 本项目的 RAG corpus → dzcmemory-web 古籍依据增强 | 高 | 高（但 dzcmemory-web 是只读）|

---

*本文件随项目演进更新。最近更新：2026-06-18（P3 完成时）*
