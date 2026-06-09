"""Profession profiles: career archetypes mapped to Bazi/divination patterns.

Each profession profile includes:
- name: Chinese and English names
- favorable_elements: which elements are beneficial for this profession
- key_ten_gods: which ten-god types indicate talent for this field
- key_shensha: which symbolic stars support this career
- element_bias: the dominant element tendency
- traits: personality traits associated with this profession
- advice: career advice rules derived from classical interpretation
- caution: things to watch for

Usage:
    from divination.knowledge.professions import match_professions
    results = match_professions(chart)  # Returns scored matches
"""

PROFESSIONS = [
    {
        "id": "tech_engineering",
        "name_zh": "科技/工程",
        "name_en": "Technology & Engineering",
        "favorable_elements": ["metal", "water"],
        "key_ten_gods": ["食伤", "偏印"],
        "key_shensha": ["文昌", "学堂"],
        "element_bias": "金水相生",
        "traits": ["逻辑思维", "钻研精神", "创新力", "动手能力"],
        "advice": [
            "金水相生之局，宜从事精密技术、计算机、机械工程等需要逻辑推理的工作。",
            "食伤吐秀之人，适合研发创新类岗位，持续学习新技术是优势所在。",
            "偏印为用，适合深度钻研型工作，不宜频繁更换方向。",
        ],
        "caution": [
            "忌火土过重之运，技术迭代压力大时需注意调节。",
            "与人协作需刻意练习沟通能力。",
        ],
    },
    {
        "id": "business_finance",
        "name_zh": "商业/金融",
        "name_en": "Business & Finance",
        "favorable_elements": ["water", "metal"],
        "key_ten_gods": ["财星", "官星"],
        "key_shensha": ["天乙贵人", "金舆"],
        "element_bias": "水金流通",
        "traits": ["商业头脑", "风险把控", "人际网络", "决断力"],
        "advice": [
            "财星得用，宜从事金融、投资、贸易等资金流转快的行业。",
            "天乙贵人临命，商业合作中多有贵人相助，需善用人脉。",
            "金舆星照，适合需要频繁出差或涉及交通物流的商业方向。",
        ],
        "caution": [
            "财旺身弱需防范财务风险，不宜过度杠杆。",
            "比劫夺财之年需谨慎合伙和投资。",
        ],
    },
    {
        "id": "creative_arts",
        "name_zh": "创意/艺术",
        "name_en": "Creative & Arts",
        "favorable_elements": ["wood", "fire"],
        "key_ten_gods": ["食伤"],
        "key_shensha": ["华盖", "桃花"],
        "element_bias": "木火通明",
        "traits": ["创造力", "审美力", "表现力", "感性思维"],
        "advice": [
            "食伤泄秀得力，木火通明之局，宜从事设计、影视、文学、音乐等创意行业。",
            "华盖入命，有独特的艺术天赋和精神追求，适合独立创作。",
            "桃花星照，人缘佳、有感染力，适合面向公众的艺术表现形式。",
        ],
        "caution": [
            "食伤过旺需防情绪起伏大，建立创作纪律很重要。",
            "忌金水过重之运压制创造力，低谷期需耐心等待。",
        ],
    },
    {
        "id": "politics_law",
        "name_zh": "政治/法律",
        "name_en": "Politics & Law",
        "favorable_elements": ["fire", "earth"],
        "key_ten_gods": ["官杀", "印星"],
        "key_shensha": ["天乙贵人", "将星"],
        "element_bias": "火土相生",
        "traits": ["正义感", "领导力", "规则意识", "抗压能力"],
        "advice": [
            "官印相生格局，宜从政、司法、公务员等体制内发展方向。",
            "将星入命，有统帅才能，适合管理岗位和领导角色。",
            "天乙贵人临，仕途易得上级赏识和提拔。",
        ],
        "caution": [
            "官杀混杂需注意权力边界，谨防官非。",
            "伤官见官之年宜低调行事。",
        ],
    },
    {
        "id": "medicine_healing",
        "name_zh": "医疗/健康",
        "name_en": "Medicine & Healthcare",
        "favorable_elements": ["wood", "fire"],
        "key_ten_gods": ["印星", "食伤"],
        "key_shensha": ["天医", "天乙贵人"],
        "element_bias": "木火平衡",
        "traits": ["救人之心", "同理心", "细致入微", "科学素养"],
        "advice": [
            "印星为用，宜从事医疗、护理、心理咨询等助人行业。",
            "食神制杀之象，适合外科、急救等需要果断处理能力的方向。",
            "五行较为平衡之人适合中医调理、养生保健等综合性健康工作。",
        ],
        "caution": [
            "医疗行业责任重大，需持续进修保持专业水准。",
            "需注意自身健康管理，避免过劳。",
        ],
    },
    {
        "id": "education_academia",
        "name_zh": "教育/学术",
        "name_en": "Education & Academia",
        "favorable_elements": ["metal", "water"],
        "key_ten_gods": ["印星", "文昌"],
        "key_shensha": ["学堂", "文昌"],
        "element_bias": "金水主智",
        "traits": ["好学", "表达力", "耐心", "博闻强识"],
        "advice": [
            "金水主智，文昌学堂入命，宜从事教育、科研、出版等知识密集型行业。",
            "印星得用，适合高等教育、学术研究等需要深厚理论功底的方向。",
            "华盖加文昌，在哲学、历史、文化研究领域有独特优势。",
        ],
        "caution": [
            "学术路径需耐得住寂寞，忌急功近利。",
            "食伤受制时需注意教学表达方式的调整。",
        ],
    },
    {
        "id": "military_security",
        "name_zh": "军警/安保",
        "name_en": "Military & Security",
        "favorable_elements": ["metal", "fire"],
        "key_ten_gods": ["七杀", "羊刃"],
        "key_shensha": ["将星", "魁罡"],
        "element_bias": "金火锻钢",
        "traits": ["果敢", "纪律性", "责任感", "体魄强健"],
        "advice": [
            "七杀得制可掌权柄，宜军警、消防、安保等纪律部队方向。",
            "魁罡加羊刃，天生刚毅果决，适合需要快速决策的高压岗位。",
            "将星照命，有军事领导才能。",
        ],
        "caution": [
            "羊刃过旺需防意外伤害，宜加强安全防护意识。",
            "刚极易折，需培养柔和的沟通方式。",
        ],
    },
    {
        "id": "sales_marketing",
        "name_zh": "销售/市场",
        "name_en": "Sales & Marketing",
        "favorable_elements": ["fire", "water"],
        "key_ten_gods": ["财星", "食伤"],
        "key_shensha": ["桃花"],
        "element_bias": "火水既济",
        "traits": ["沟通力", "感染力", "抗压力", "灵活变通"],
        "advice": [
            "食伤生财格局，宜销售、市场营销、公关等需要强沟通力的行业。",
            "桃花入命人缘佳，客户关系和商务拓展有天然优势。",
            "驿马逢财，适合需要出差或跑动的销售岗位，动中求财。",
        ],
        "caution": [
            "比劫夺财之运需防范客户流失和业绩波动。",
            "需注意过度承诺的风险。",
        ],
    },
    {
        "id": "entrepreneurship",
        "name_zh": "创业/企业家",
        "name_en": "Entrepreneurship",
        "favorable_elements": ["wood", "water"],
        "key_ten_gods": ["财星", "官星", "食伤"],
        "key_shensha": ["天乙贵人", "金舆", "驿马"],
        "element_bias": "水木清华",
        "traits": ["冒险精神", "大局观", "执行力", "资源整合"],
        "advice": [
            "食伤生财加官星护财，格局具备创业者的完整能力链。",
            "驿马金舆齐现，适合跨地域经营、国际贸易等有空间幅度的商业模式。",
            "天乙贵人临命，创业路上易获贵人投资和资源支持。",
        ],
        "caution": [
            "身弱财旺不宜急于扩张，先固本再图大。",
            "官杀混杂时需注意合规和法律风险。",
        ],
    },
    {
        "id": "service_hospitality",
        "name_zh": "服务/餐饮/酒店",
        "name_en": "Service & Hospitality",
        "favorable_elements": ["fire", "earth"],
        "key_ten_gods": ["食伤", "财星"],
        "key_shensha": ["红鸾", "天喜"],
        "element_bias": "火土敦厚",
        "traits": ["服务意识", "热情", "细致", "团队协作"],
        "advice": [
            "火土相生敦厚有礼，宜高端酒店、餐饮、旅游等服务业。",
            "红鸾天喜照命，善于营造温馨体验，适合与人打交道的工作。",
            "食伤吐秀，在美食、设计、体验方面有独特品味。",
        ],
        "caution": [
            "服务业压力大，需注意身体透支和情绪管理。",
            "水旺之年可能客源波动。",
        ],
    },
    {
        "id": "agriculture_environment",
        "name_zh": "农业/环保",
        "name_en": "Agriculture & Environment",
        "favorable_elements": ["wood", "earth"],
        "key_ten_gods": ["印星", "食伤"],
        "key_shensha": ["华盖"],
        "element_bias": "木土根基",
        "traits": ["自然亲和", "耐心", "实操力", "可持续发展观"],
        "advice": [
            "木土相得，宜生态农业、园艺、环保工程等亲近自然的行业。",
            "印星为用，适合需要长期耕耘和耐心的事业方向。",
            "华盖入命，在生态哲学和可持续设计方面有深刻见解。",
        ],
        "caution": [
            "金克木之运需注意自然灾害风险。",
            "行业回报周期长，需有稳定资金支持。",
        ],
    },
    {
        "id": "sports_athletics",
        "name_zh": "体育/竞技",
        "name_en": "Sports & Athletics",
        "favorable_elements": ["metal", "fire"],
        "key_ten_gods": ["比劫", "七杀"],
        "key_shensha": ["将星", "羊刃"],
        "element_bias": "金火争锋",
        "traits": ["竞争心", "耐力", "专注力", "团队精神"],
        "advice": [
            "身强比劫旺，骨架坚实，适合职业体育、竞技比赛等对抗性强的领域。",
            "羊刃加将星，天生有竞争意识和不服输的精神。",
            "七杀制得宜者，在高压竞技环境下反而能超常发挥。",
        ],
        "caution": [
            "羊刃逢冲之年需防运动伤害。",
            "竞技生涯有年龄限制，需规划退役后发展。",
        ],
    },
    {
        "id": "media_entertainment",
        "name_zh": "传媒/娱乐",
        "name_en": "Media & Entertainment",
        "favorable_elements": ["fire", "water"],
        "key_ten_gods": ["食伤", "财星"],
        "key_shensha": ["桃花", "红鸾"],
        "element_bias": "火水映照",
        "traits": ["表现力", "舞台魅力", "话题制造", "潮流敏感"],
        "advice": [
            "水火既济，宜影视演艺、新媒体、广告等需要表现力和感染力的行业。",
            "桃花带食伤者，镜头感和观众缘俱佳。",
            "驿马临财，适合需要流动取景、巡回演出的传媒方向。",
        ],
        "caution": [
            "桃花混杂需注意舆论风险和隐私保护。",
            "水火交战之运可能面临公众评价两极分化。",
        ],
    },
    {
        "id": "religion_spirituality",
        "name_zh": "宗教/玄学/身心灵",
        "name_en": "Spirituality & Metaphysics",
        "favorable_elements": ["water", "fire"],
        "key_ten_gods": ["偏印", "食伤"],
        "key_shensha": ["华盖", "空亡"],
        "element_bias": "水火既济",
        "traits": ["灵性感知", "深度思考", "共情力", "超然心态"],
        "advice": [
            "华盖加空亡，天生对形而上领域有深刻理解，宜宗教研究、心理咨询、身心灵疗愈。",
            "偏印为用，适合命理、占星、冥想教师等需要灵性洞察的方向。",
            "水火既济，在玄学和现代心理学的交叉领域有独特优势。",
        ],
        "caution": [
            "空亡过重需保持现实感，避免陷入虚无。",
            "需平衡精神追求与物质生活。",
        ],
    },
    {
        "id": "government_civil_service",
        "name_zh": "公务员/事业单位",
        "name_en": "Civil Service",
        "favorable_elements": ["earth", "fire"],
        "key_ten_gods": ["官星", "印星"],
        "key_shensha": ["天乙贵人", "将星"],
        "element_bias": "火土稳重",
        "traits": ["稳重", "服从意识", "文字功底", "大局观"],
        "advice": [
            "官印相生格局稳健，宜考公、事业单位、国企等稳定发展路径。",
            "火土相生之局，体制内能获得持续发展和晋升。",
            "天乙贵人照命，职场中易遇提携之贵人。",
        ],
        "caution": [
            "伤官见官之年需谨言慎行，防范人事纠纷。",
            "官杀混杂时不宜轻易跳槽。",
        ],
    },
    {
        "id": "freelance_consulting",
        "name_zh": "自由职业/咨询",
        "name_en": "Freelance & Consulting",
        "favorable_elements": ["water", "wood"],
        "key_ten_gods": ["食伤", "偏印"],
        "key_shensha": ["驿马", "文昌"],
        "element_bias": "水木灵动",
        "traits": ["独立", "专业深度", "灵活应变", "学习力"],
        "advice": [
            "食伤配偏印，技术深度与表达能力兼具，宜自由职业、独立咨询、远程工作。",
            "驿马临命，适合不受地域限制的线上自由职业模式。",
            "文昌星照，知识付费和在线教育领域有发展潜力。",
        ],
        "caution": [
            "财源不稳定是常态，需建立多个收入渠道。",
            "孤辰寡宿者需注意社交隔离，主动维护人际网络。",
        ],
    },
]


def match_professions(chart, top_n: int = 5) -> list[dict]:
    """Match a chart against all profession profiles and return top N fits.

    Args:
        chart: A ChartResult from bazi or bazi_v2 engine
        top_n: Number of top matches to return

    Returns:
        [{profession: ..., score: 0-100, match_details: ..., advice: [...]}, ...]
    """
    raw = chart.raw or {}
    elements = chart.normalized.get("elements", {})
    pattern_data = raw.get("pattern", {})
    yong_shen = raw.get("yong_shen", {})
    shensha = raw.get("shensha", {})

    results = []
    for prof in PROFESSIONS:
        score = 0.0
        details = []

        # 1. Element match (weight: 40)
        fav_elements = prof.get("favorable_elements", [])
        if fav_elements:
            element_total = sum(elements.values()) or 1.0
            elem_score = 0.0
            for elem in fav_elements:
                elem_score += elements.get(elem, 0.0) / element_total
            score += min(elem_score * 50, 40)
            if elem_score > 0.3:
                details.append(f"五行匹配({'+'.join(fav_elements)})")

        # 2. Ten god match (weight: 25)
        ten_gods = raw.get("strength_basis", {})
        key_gods = prof.get("key_ten_gods", [])
        if key_gods and ten_gods:
            god_score = 0.0
            for god in key_gods:
                # Check if this ten god is present and counts
                count = 0
                if god in raw.get("seasonal_strength_reference", {}).get("ten_god_counts", {}):
                    count = raw["seasonal_strength_reference"]["ten_god_counts"].get(god, 0)
                if count >= 2:
                    god_score += 8
                elif count >= 1:
                    god_score += 5
            score += min(god_score, 25)
            if god_score > 0:
                details.append(f"十神配置({'+'.join(key_gods)})")

        # 3. Shensha match (weight: 20)
        key_shensha_names = prof.get("key_shensha", [])
        if key_shensha_names and shensha:
            stars = shensha.get("stars", [])
            star_names = {s["star"] for s in stars}
            matches = key_shensha_names & star_names if isinstance(key_shensha_names, set) else \
                      [s for s in key_shensha_names if s in star_names]
            if matches:
                star_score = min(len(matches) * 6, 20)
                score += star_score
                details.append(f"神煞契合({', '.join(matches)})")

        # 4. Yong Shen alignment (weight: 15)
        yong_primary = yong_shen.get("primary", [])
        if yong_primary:
            aligned = [e for e in yong_primary if e in fav_elements]
            if aligned:
                align_score = min(len(aligned) * 7, 15)
                score += align_score
                details.append(f"用神适配({', '.join(aligned)})")

        score = round(min(score, 98), 1)
        results.append({
            "profession_id": prof["id"],
            "profession": prof["name_zh"],
            "profession_en": prof["name_en"],
            "score": score,
            "match_details": details,
            "advice": prof["advice"],
            "caution": prof["caution"],
            "traits": prof["traits"],
            "element_bias": prof["element_bias"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def get_profession_advice(profession_id: str) -> dict | None:
    """Get advice for a specific profession by ID."""
    for prof in PROFESSIONS:
        if prof["id"] == profession_id:
            return {
                "name_zh": prof["name_zh"],
                "advice": prof["advice"],
                "caution": prof["caution"],
                "traits": prof["traits"],
            }
    return None
