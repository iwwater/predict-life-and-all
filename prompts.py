"""解读层核心：读法规范(系统提示) + 各法盘面序列化 + 用户提示构建。
方法论借鉴 yuan 的保守读法：传统文化视角、给倾向与建议而非断言、
多法分歧时并陈不同视角、不包装成科学、不替代专业建议。"""
from ..contracts import ChartResult

SYSTEM_PROMPT = """你是一位融通中西的玄学解读助手。请严格遵守以下原则：

【立场】以传统文化与符号象征的视角提供解读，这是文化与自我反思的工具，不是科学预测，也不能替代医疗、法律、财务等专业意见。

【口径】用"倾向、常见、容易、可留意、建议"等措辞，禁止使用"注定、必然、一定、绝对、肯定会"等绝对化表达。不制造焦虑，不做恐吓式断语（如重病、死亡、灾祸）。涉及健康/法律/财务的具体决定，提示咨询专业人士。

【结构】先给整体印象，再分项（性格特质 / 事业财运 / 感情关系 / 当前阶段与未来五年倾向），最后给 2-3 条温和、可执行的建议。

【中西合参】当给出多种术数时：相互印证之处可加强说明；分歧之处要如实并陈"从X法看…，从Y法看…"，不要强行统一成单一结论。

【依据】只依据下方排盘事实推演，不杜撰盘面没有的信息。引用古籍义理时点明出处概念。"""

DISCLAIMER = "（以上为传统文化象征视角的参考，非科学预测，重大决定请结合现实并咨询专业人士。）"


def _serialize(c: ChartResult) -> str:
    r = c.raw
    m = c.method
    if m == "bazi":
        p = r["pillars"]; j = r.get("断", {})
        return (f"【八字四柱】年{p['year']} 月{p['month']} 日{p['day']} 时{p['hour']}；"
                f"日主{r.get('day_master')}。五行：{c.normalized.get('elements')}。"
                f"粗判：{j.get('粗断','')}，最旺{j.get('最旺五行','')}，缺{j.get('缺失五行',[])}。"
                f"大运：{[t['label'] for t in c.normalized.get('timeline',[])][:4]}")
    if m == "ziwei":
        return (f"【紫微斗数】命主{r.get('soul')}、身主{r.get('body')}、五行局{r.get('five_elements','')}；"
                f"命宫主星：{next((p['major_stars'] for p in r.get('palaces',[]) if p['name']=='命宫'),[])}")
    if m == "qimen":
        j = r.get("断", {})
        return (f"【奇门遁甲】{r['排局']}（{r['节气']}）；值符值使：{r['值符值使']}；"
                f"格局：{j.get('格局',[])}；门状态：{j.get('门状态',{})}；空亡宫：{j.get('空亡宫',[])}")
    if m == "liuyao":
        j = r.get("断", {})
        return (f"【六爻】本卦{r['本卦']['name']}（{r['宫']}宫，世{r['世']}应{r['应']}）"
                f"动爻{r['动爻']}变{r['变卦']['name'] if r['变卦'] else '无'}；"
                f"断：{j.get('断语', j.get('提示',''))}")
    if m == "meihua":
        j = r.get("断", {})
        return (f"【梅花易数】主卦{r['主卦']['name']}/互{r['互卦']['name']}/变{r['变卦']['name']}；"
                f"体{r['体卦']}用{r['用卦']}；体用断：{j.get('总断')}（{j.get('断语','')}）")
    if m == "chenggu":
        return f"【称骨】总骨重{r['总骨重_两']}两；批语：{r['批语首句']}"
    if m == "bazhai":
        return f"【八宅】{r['命卦']}命（{r['命']}）；吉方{r['吉方']}；凶方{r['凶方']}"
    if m == "xuankong":
        return f"【玄空飞星】{r['运']}运 {r['坐']}山{r['向']}向；格局{r['格局']}；向首{r['向首']} 坐山{r['坐山']}"
    if m == "western":
        pl = {k: f"{v['sign']}{round(v['degree'])}°" for k, v in r["planets"].items()}
        return (f"【西方占星】上升{r['ascendant']['sign'] if r['ascendant'] else '?'}，"
                f"天顶{r['midheaven']['sign'] if r.get('midheaven') else '?'}；行星{pl}；"
                f"主要相位{[(a['a'],a['b'],a['aspect']) for a in r['aspects'][:6]]}")
    if m == "vedic":
        pl = {k: f"{v['宫Rashi']}/{v['宿Nakshatra']}/D9{v['九分盘D9']}/{v['庙旺落陷']}"
              for k, v in r["planets"].items()}
        d = r.get("Vimshottari大运", {})
        cur = d.get("当前大运") or {}
        cur_sub = cur.get("副周期Antardasha", [])
        cur_s = next((x['副星'] for x in cur_sub if x['起'] <= '2026-06' <= x['止']), "")
        return (f"【吠陀占星】(Lahiri{r['ayanamsa']}°) 行星宫/宿/D9/庙陷：{pl}；"
                f"当前大运 {cur.get('主星','')}({cur.get('起','')}~{cur.get('止','')})"
                + (f"，副周期{cur_s}" if cur_s else ""))
    if m == "tarot":
        cards = [f"{c2['位置']}={c2['牌']}({c2['方位']}:{c2['牌义']}"
                 + (f",占星{c2['占星']}" if c2.get('占星') else "") + ")" for c2 in r["牌面"]]
        an = r.get("牌组分析", {})
        return (f"【塔罗·{r.get('牌阵名称', r['牌阵'])}】" + "；".join(cards)
                + f"。牌组：大牌{an.get('大牌数')}/逆位{an.get('逆位数')}/宫廷{an.get('宫廷牌数')}，"
                + f"提示：{an.get('整体提示',[])}。"
                + f"\n  ※本阵解读要领（必须按此位置关系读，勿孤立断单张）：{r.get('解读要领','')}")
    if m == "numerology":
        return f"【数字命理】生命灵数{r['生命灵数']}（{r['释义']}）" + (f"，命运数{r.get('命运数')}" if r.get('命运数') else "")
    return f"【{m}】{r}"


def build_messages(charts: list[ChartResult], question: str | None = None) -> dict:
    facts = "\n".join(_serialize(c) for c in charts)
    methods = "、".join(dict.fromkeys(c.method for c in charts))
    q = f"\n\n【求测者所问】{question}" if question else ""
    multi = "（已提供多种术数，请中西合参，印证与分歧都要说明）" if len(charts) > 1 else ""
    user = f"以下是为求测者排出的盘面（{methods}）{multi}：\n\n{facts}{q}\n\n请按系统规则给出解读。"
    return {"system": SYSTEM_PROMPT, "user": user}
