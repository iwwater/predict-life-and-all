"""解读层核心:读法规范(系统提示) + 各法盘面序列化 + 古籍注入。"""
from ..contracts import ChartResult

SYSTEM_PROMPT = """你是一位融通中西的玄学解读助手。请严格遵守以下原则:

【立场】以传统文化与符号象征的视角提供解读，这是文化与自我反思的工具，不是科学预测，也不能替代医疗、法律、财务等专业意见。

【口径】用"倾向、常见、容易、可留意、建议"等措辞，禁止使用"注定、必然、一定、绝对、肯定会"等绝对化表达。不制造焦虑，不做恐吓式断语。涉及健康/法律/财务的具体决定，提示咨询专业人士。

【时态与年份】可以据盘面中的大运、流年等具体年份进行推演解读，这正是用户关心的核心内容。但措辞必须用"倾向、可能、容易、可留意"等推测语气，禁止用"注定、必然、一定会"等绝对化表达断言某年某事。过去年份的盘面信息可作为性格形成和格局变化的背景解释。

【结构】严格按以下顺序输出(Markdown):
### 整体印象
1-2 句话概括盘面给人的核心感受。

### 性格特质
基于盘面事实(如日主、太阳星座、五行强弱等)推演性格轮廓，含优势和盲点各 2-3 点。

### 事业与方向
结合大运、相位、格局等，给出事业倾向和当前阶段的建议。不断言具体职位或收入。

### 感情与人际
如有相关字段(桃花/合冲/关系宫位等)，温和解读关系模式。如盘面无感情数据则本节省略。

### 当前提示与建议
2-3 条具体可执行的小建议，每条 20-40 字，温和、正向、留选择的余地。

【中西合参】当给出多种术数时:相互印证之处可加强说明;分歧之处要如实并陈"从 X 法看...，从 Y 法看..."，不要强行统一成单一结论。

【古籍依归】引用古籍义理时注明出处，如「《渊海子平》:日主者乃八字之主宰也」；不要凭空引用不存在的古籍名。古籍仅供参照义理，不代表绝对真理。

【依据】只依据下方排盘事实推演，不杜撰盘面没有的信息。不预测具体事件日期、不指定具体数值(如金额、排名)。

【输出格式】直接从"### 整体印象"开始，严禁任何开场白或确认语（如"好的""请允许我""我会遵守""根据您的要求""以下是解读"等）。第一个字必须是"### 整体印象"，不要复述系统规则。"""

DISCLAIMER = "\n\n(以上为传统文化象征视角的参考，非科学预测，重大决定请结合现实并咨询专业人士。)"


def _serialize(c):
    """全量盘面序列化:不再截断,输出所有可用信息。"""
    r = c.raw or {}
    m = c.method
    try:
        if m in ("bazi", "bazi_v2"):
            pillars = r.get("pillars", {})
            pd = r.get("pillar_details", [])
            dm = r.get("day_master", "?")
            tl = [t["label"] for t in c.normalized.get("timeline", [])]
            score = r.get("strength_score")
            sb = r.get("strength_basis", {})
            cl = r.get("current_luck", {})
            ai = r.get("annual_interactions", {})
            ls = r.get("life_stage", {})
            parts = [
                f"【八字四柱{'·精算版' if m == 'bazi_v2' else ''}】年{pillars.get('year','?')} 月{pillars.get('month','?')} 日{pillars.get('day','?')} 时{pillars.get('hour','?')}",
                f"日主:{dm}，身强评分:{score}/100" if score is not None else f"日主:{dm}",
            ]
            if sb:
                parts.append(f"同党(比劫{sb.get('peer_count',0)}+印星{sb.get('resource_count',0)}) 异党(食伤{sb.get('output_count',0)}+官杀{sb.get('official_count',0)}+财{sb.get('wealth_count',0)}) 月令分{sb.get('month_strength','')}")
            if pd:
                for p in pd:
                    hs = p.get("hidden_stems", [])
                    shigan = p.get("ten_god_stem", "")
                    shizhi = p.get("ten_god_branch", [])
                    gs = p.get("growth_stage", "")
                    parts.append(f"{p['label']}:{p['ganzhi']} 五行{p.get('wuxing','')}" +
                                (f" 藏干:{'/'.join(hs)}" if hs else "") +
                                (f" 十神(干):{shigan}" if shigan else "") +
                                (f" 十神(支):{'/'.join(shizhi)}" if shizhi else "") +
                                (f" 长生:{gs}" if gs else ""))
            # ── v2 fields ──
            pattern_data = r.get("pattern", {})
            if pattern_data:
                parts.append(f"格局:{pattern_data.get('pattern','?')}({pattern_data.get('description','')})")
            yong_shen = r.get("yong_shen", {})
            if yong_shen:
                parts.append(f"用神:{yong_shen.get('rationale','')}")
            ysq = r.get("yong_shen_quality", {})
            if ysq:
                parts.append(f"用神质量:{ysq.get('score',0)}/100 ({ysq.get('level','')}) — {ysq.get('analysis','')}")
            shensha_data = r.get("shensha", {})
            if shensha_data:
                ss = shensha_data.get("summary", {})
                notable = ss.get("notable", [])
                if notable:
                    parts.append(f"关键神煞:{', '.join(notable)}")
                stars_detail = shensha_data.get("stars", [])
                if stars_detail:
                    star_lines = []
                    for s in stars_detail:
                        star_lines.append(f"  {s['star']}({s['category']})@{s.get('found_in','')}柱: {s['meaning'][:80]}")
                    parts.append("全部神煞:\n" + "\n".join(star_lines[:15]))
            element_flow = r.get("element_flow", {})
            if element_flow:
                flow_summary = element_flow.get("interpretation", "")
                if flow_summary:
                    parts.append(f"五行流转:{flow_summary}")
            if cl and cl.get("decade_ganzhi"):
                parts.append(f"当前大运:{cl['decade_ganzhi']}({cl.get('decade_from','')}-{cl.get('decade_to','')}) 流年:{cl.get('annual_label','')}")
            if ai and ai.get("interactions"):
                parts.append("流年互动:" + "; ".join(i.get("note", "") for i in ai["interactions"]))
            if ls and ls.get("stages"):
                parts.append("12长生:" + " ".join(s["pillar"]+"->"+s["stage"] for s in ls["stages"]))
            parts.append(f"五行:{c.normalized.get('elements',{})} 大运:{tl[:6]}")
            refs = r.get("calculation_basis", {}).get("references", [])
            if refs:
                parts.append("【古籍参考】" + "; ".join(f"《{rf['source']}》" for rf in refs[:3]))
            return "\n".join(parts)

        if m == "ziwei":
            palaces = r.get("palaces", [])
            parts = [
                f"【紫微斗数】命主{r.get('soul','?')}，身主{r.get('body','?')}，五行局{r.get('five_elements_class','')}",
            ]
            for p in palaces[:12]:
                stars = "/".join(p.get("major_stars", []) + p.get("minor_stars", []))
                parts.append(f"{p.get('name','?')}宫: {stars or '空宫'}")
            h = r.get("horoscope", {})
            for period in ["decadal", "yearly", "monthly"]:
                item = h.get(period, {})
                if item:
                    mut = "/".join(item.get("mutagen", []))
                    parts.append(f"{period}:{item.get('ganzhi','')} 四化:{mut}")
            return "\n".join(parts)

        if m == "qimen":
            parts = [
                f"【奇门遁甲】{r.get('dun','')}{r.get('yuan','')}{r.get('ju','')}局",
                f"节气:{r.get('solar_term','')} 旬首:{r.get('xun_shou','')}",
                f"值符:{r.get('zhifu',{}).get('star','')}落{r.get('zhifu',{}).get('star_gong','')} 值使:{r.get('zhifu',{}).get('door','')}落{r.get('zhifu',{}).get('door_gong','')}",
            ]
            pattern = r.get("pattern_analysis", {})
            if pattern:
                parts.append(f"格局:{pattern.get('overall_label','')}")
                for g in pattern.get("patterns", []):
                    parts.append(f"  {g['gong']}:{g['name']}({g['type']})")
            return "\n".join(parts)

        if m == "western":
            planets = r.get("planets", {})
            aspects = r.get("aspects", [])
            asc = r.get("ascendant", {})
            houses = r.get("houses", [])
            parts = [
                f"【西方占星】上升:{asc.get('sign','?')}{asc.get('degree',0):.1f}",
                "行星落位:" + " ".join(f"{k}={v.get('sign','?')}{v.get('degree',0):.1f}" for k, v in planets.items()),
                "相位:" + "; ".join(f"{a['a']}{a['aspect']}{a['b']}({a.get('orb',0):.1f})" for a in aspects),
            ]
            if houses:
                parts.append("宫位(Whole Sign):" + " ".join(f"H{i+1}={h.get('sign','?')}" for i, h in enumerate(houses[:12])))
            return "\n".join(parts)

        if m == "vedic":
            planets = r.get("planets", {})
            parts = [
                f"【吠陀占星】Lahiri 岁差:{r.get('ayanamsa','?')}",
                "行星:" + " ".join(f"{k}={v.get('sign','?')}{v.get('degree',0):.1f}" for k, v in planets.items()),
            ]
            return "\n".join(parts)

        if m == "tarot":
            cards = r.get("cards", [])
            parts = [f"【塔罗-{r.get('spread_name', r.get('spread',''))}】"]
            for ca in cards:
                parts.append(f"{ca.get('position','')}: {ca.get('name','')}({ca.get('orient','')}) {ca.get('keywords','')}")
            return "\n".join(parts)

        if m == "numerology":
            return f"【数字命理】生命灵数:{r.get('life_path','')} 命运数:{r.get('expression','')} 周期:{r.get('current_cycle','')}"

        if m == "lenormand":
            cards = r.get("cards", [])
            analysis = r.get("analysis", {})
            parts = [f"【雷诺曼-{r.get('spread_name', r.get('spread', ''))}】(36张牌, 无逆位)"]
            for ca in cards:
                parts.append(f"{ca.get('position','')}: {ca.get('name','')}({ca.get('name_zh','')}) {ca.get('core_meaning','')}")
            if analysis.get("pairs"):
                parts.append("关键组合:")
                for p in analysis["pairs"][:5]:
                    parts.append(f"  {p['card_a']}+{p['card_b']}: {p['combined']}")
            parts.append(f"牌面氛围: 阳{analysis.get('positive_count',0)}/阴{analysis.get('negative_count',0)}/中{analysis.get('neutral_count',0)}")
            return "\n".join(parts)

        if m == "liuren":
            parts = [
                f"【大六壬】月将{r.get('divination_time',{}).get('month_general_name','')}({r.get('divination_time',{}).get('month_general','')}) 占时{r.get('divination_time',{}).get('hour_branch','')}",
                f"日干: {r.get('day_ganzhi','')}  旬空: {r.get('xun_kong','')}",
                f"四课: " + " | ".join(
                    f"课{l['idx']}:{l['upper']}→{l['lower']}" for l in r.get("four_lessons", [])
                ),
                f"三传: {r.get('three_transmissions',{}).get('chu_chuan','?')}→{r.get('three_transmissions',{}).get('zhong_chuan','?')}→{r.get('three_transmissions',{}).get('mo_chuan','?')} ({r.get('three_transmissions',{}).get('method','')})",
                f"贵人: {r.get('gui_ren_zhi','')}",
            ]
            generals = r.get("twelve_generals", [])
            if generals:
                parts.append("十二天将: " + " ".join(
                    f"{g['general']}({g['tian_pan_zhi']})" for g in generals[:6]
                ))
            return "\n".join(parts)

        if m == "liuyao":
            lines = r.get("hex_lines", [])
            parts = [f"【六爻】本卦:{r.get('ben_gua','')} 变卦:{r.get('bian_gua','')}",
                     f"用神:{r.get('using_god','')} 依据:{r.get('using_god_basis','')}"]
            for li in lines:
                parts.append(f"爻{li.get('pos','')}:{'阳' if li.get('yang') else '阴'} {li.get('gan_zhi','')} {li.get('liu_qin','')} {li.get('liu_shen','')}")
            return "\n".join(parts)

        if m == "meihua":
            return f"【梅花易数】主卦:{r.get('zhu_gua','')}/互:{r.get('hu_gua','')}/变:{r.get('bian_gua','')} 体:{r.get('ti_gua','')}用:{r.get('yong_gua','')} 断:{r.get('duan','')}"

        if m == "chenggu":
            return f"【称骨】总骨重:{r.get('total_liang',0)}两 批语:{r.get('piyu','')}"

        if m == "bazhai":
            parts = [
                f"【八宅明镜】命卦:{r.get('life_gua','')}({r.get('life_gua_number','')}数) {'东四命' if r.get('is_east') else '西四命'}",
                f"立春年份:{r.get('ritual_year','')} 年柱:{r.get('year_gz','')}",
                f"四吉方:{', '.join(r.get('auspicious_dirs',[]))}  四凶方:{', '.join(r.get('inauspicious_dirs',[]))}",
            ]
            hg = r.get("house_gua")
            if hg:
                he = "东四宅" if r.get("house_is_east") else "西四宅"
                parts.append(f"宅卦:{hg}({he}) 坐山:{r.get('sitting','')}")
                match_info = r.get("house_resident_match", {})
                if match_info:
                    parts.append(f"宅命相配:{'✓ 相配' if match_info.get('matched') else '✗ 不配'} ({match_info.get('level','')}) {match_info.get('description','')}")
                stars = r.get("bazhai_stars", {})
                if stars:
                    star_lines = []
                    for d, s in sorted(stars.items(), key=lambda x: x[1].get("rank", 9)):
                        marker = "吉" if s.get("auspicious") else "凶"
                        star_lines.append(f"{d}:{s['star']}({marker}#{s.get('rank','')})")
                    parts.append("大游年八星:" + " | ".join(star_lines))
            return "\n".join(parts)

        if m == "xuankong":
            parts = [
                f"【玄空飞星】{r.get('period','')} 三元九运第{r.get('period_number','')}运",
                f"坐{r.get('sitting','')}({r.get('sitting_gua','')}卦) 向{r.get('facing','')}({r.get('facing_gua','')}卦) 格局:{r.get('pattern','')}",
            ]
            tl = r.get("star_timeliness", {})
            if tl:
                legend = tl.get("legend", {})
                parts.append(f"旺衰体系: 当运五行为{tl.get('period_wuxing','')} " +
                            " ".join(f"{k}={v}" for k, v in legend.items()))
            grid = r.get("grid", {})
            if grid:
                for gua in ["坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离"]:
                    g = grid.get(gua, {})
                    if g:
                        parts.append(
                            f"{gua}宫: 运{g.get('运','?')}({g.get('运_旺衰','')}) "
                            f"山{g.get('山','?')}({g.get('山_旺衰','')}) "
                            f"向{g.get('向','?')}({g.get('向_旺衰','')})"
                        )
            return "\n".join(parts)

        if m == "tieban":
            pillars = r.get("four_pillars", {})
            encoding = r.get("encoding", {})
            verse_result = r.get("verse_result", {})
            parts = [
                f"【铁板神数】条文集数:{r.get('verse_set_number','')}",
                f"四柱: 年{pillars.get('year','?')} 月{pillars.get('month','?')} 日{pillars.get('day','?')} 时{pillars.get('hour','?')}",
                f"基数:{r.get('base_number','')}  刻分:第{r.get('ke_fen',{}).get('ke','?')}刻{r.get('ke_fen',{}).get('fen','?')}分",
            ]
            enc = encoding.get("stems", {})
            if enc:
                stem_line = "天干编码: " + " ".join(
                    f"{k}:{enc[k].get('gan','?')}={enc[k].get('num','?')}" for k in ["year", "month", "day", "hour"]
                )
                parts.append(stem_line)
            branches_enc = encoding.get("branches", {})
            if branches_enc:
                branch_line = "地支太玄数: " + " ".join(
                    f"{k}:{branches_enc[k].get('zhi','?')}({branches_enc[k].get('type','?')})={branches_enc[k].get('num','?')}"
                    for k in ["year", "month", "day", "hour"]
                )
                parts.append(branch_line)
            verses = verse_result.get("matched_verses", [])
            if verses:
                parts.append(f"匹配条文({verse_result.get('total_matched', 0)}条):")
                for v in verses:
                    parts.append(f"  【{v.get('category','')}·{v.get('number','')}】{v.get('text','')}")
            verify = verse_result.get("verification", {})
            if verify.get("note"):
                parts.append(f"校验: {verify['note']}")
            return "\n".join(parts)

    except Exception as e:
        return f"【{m}】序列化失败:{e}"

    return f"【{m}】{r}"


def _serialize_enhanced(charts, cross_validation=None, peach_blossom=None,
                        fate_modification=None, relationship_timing=None):
    """Serialize enhanced chart data including cross-validation and timing."""
    parts = []

    # Core chart data
    facts = "\n\n".join(_serialize(c) for c in charts)
    parts.append(facts)

    # Cross-validation results
    if cross_validation:
        cv = cross_validation
        parts.append("")
        parts.append("【多系统交叉验证】")
        parts.append(f"综合置信度: {cv.get('overall_confidence', '?')}/100 ({cv.get('confidence_level', '?')})")
        parts.append(f"系统间一致率: {cv.get('agreement_ratio', 0):.0%}")
        for check in cv.get("cross_checks", []):
            icon = "✓" if check.get("agree") else "✗"
            parts.append(f"  {icon} [{check.get('domain', '')}] {check.get('detail', '')}")
        for rec in cv.get("recommendations", []):
            parts.append(f"建议: [{rec.get('level', '')}] {rec.get('text', '')} → {rec.get('action', '')}")

    # Peach blossom index
    if peach_blossom:
        pb = peach_blossom
        parts.append("")
        parts.append(f"【桃花指数】{pb.get('index', '?')}/100 ({pb.get('level', '?')})")
        parts.append(f"解读: {pb.get('interpretation', '')[:200]}")

    # Relationship timing
    if relationship_timing:
        rt = relationship_timing
        parts.append("")
        parts.append(f"【感情时机】桃花位: {rt.get('peach_blossom_branch', '?')}，红鸾: {rt.get('hongluan_branch', '?')}，天喜: {rt.get('tianxi_branch', '?')}")
        for w in rt.get("prime_windows", []):
            parts.append(f"  最佳窗口: {w.get('period', '?')} (评分{w.get('relationship_score', '?')}) → {w.get('recommendation', '')}")

    # Fate modification
    if fate_modification:
        fm = fate_modification
        parts.append("")
        parts.append(f"【改运建议】{fm.get('summary', '')[:300]}")

    return "\n".join(parts)


def build_messages(charts, question=None, enhanced_data=None):
    """Build system + user messages for LLM interpretation.

    Args:
        charts: List of ChartResult objects
        question: User's question
        enhanced_data: Optional dict with cross_validation, peach_blossom,
                       fate_modification, relationship_timing
    """
    from datetime import date as _date
    today = _date.today()
    date_str = f"{today.year}年{today.month}月{today.day}日"

    # Use enhanced serialization if data available
    if enhanced_data:
        facts = _serialize_enhanced(
            charts,
            cross_validation=enhanced_data.get("cross_validation"),
            peach_blossom=enhanced_data.get("peach_blossom"),
            fate_modification=enhanced_data.get("fate_modification"),
            relationship_timing=enhanced_data.get("relationship_timing"),
        )
    else:
        facts = "\n\n".join(_serialize(c) for c in charts)

    methods = "、".join(dict.fromkeys(c.method for c in charts))
    q = f"\n\n【求测者所问】{question}" if question else ""
    multi = ("\n\n【中西合参提示】已提供多种术数，请做中西合参解读：相互印证之处可加强说明；"
             "分歧之处要如实并陈，从 X 法看...，从 Y 法看...，不要强行统一成单一结论。"
             "如果中西结论一致，请点明共识的力量；如果有分歧，请如实呈现两种视角。") if len(charts) > 1 else ""

    # 收集古籍引用
    ref_lines = []
    seen = set()
    for c in charts:
        refs = c.raw.get("calculation_basis", {}).get("references", [])
        for rf in refs:
            key = rf.get("source", "")
            if key and key not in seen:
                seen.add(key)
                ref_lines.append(f"- 《{key}》：{rf.get('excerpt','')[:100]}")

    ref_block = ""
    if ref_lines:
        ref_block = "\n\n【古籍参考】（仅供解读时参照义理，不代表绝对真理）\n" + "\n".join(ref_lines)

    user = (f"以下是为求测者排出的盘面({methods}){multi}:\n\n{facts}{q}{ref_block}"
            f"\n\n请按系统规则给出解读。要求至少包含：整体印象、性格特质、事业与方向、当前提示与建议四个部分，总字数不少于500字。"
            f"\n\n重要提示：今天是{date_str}。你只能基于盘面推演当前阶段和未来趋势，严禁声称某个具体公历年份一定会发生什么。")

    # 把日期注入 system prompt 开头
    dated_system = f"当前日期是 {date_str}。\n\n{SYSTEM_PROMPT}"
    return {"system": dated_system, "user": user}
