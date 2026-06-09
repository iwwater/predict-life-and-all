"""解读层护栏:输入风险话题转介 + 输出绝对化用语软化 + 免责声明。"""
_ABSOLUTE = ["注定", "必然", "一定会", "肯定会", "绝对", "100%",
             "百分之百", "毫无疑问", "必定"]
_SOFTEN = {
    "注定": "倾向于", "必然": "较可能", "一定会": "往往会",
    "肯定会": "多半会", "绝对": "通常", "必定": "多半",
}
_CRISIS = ["自杀", "自残", "轻生", "不想活", "活不下去", "想死"]
_MEDICAL = ["重病", "绝症", "癌症", "癌", "能不能治好", "会不会死", "寿命", "几时死"]
_LEGAL_FIN = ["官司一定", "稳赚", "买哪只股", "全仓", "梭哈", "能不能离婚", "包赚"]


def check_input(question):
    if not question:
        return {"block": False, "notes": []}
    notes = []
    if any(k in question for k in _CRISIS):
        return {
            "block": True,
            "message": ("听起来你正承受很大的痛苦。这不是算命能回答的问题,"
                        "也请不要独自承受。\n\n"
                        "中国心理援助热线:400-161-9995\n"
                        "北京心理危机研究与干预中心:010-82951332\n"
                        "或与信任的人、专业人士谈谈。"),
        }
    if any(k in question for k in _MEDICAL):
        notes.append("健康问题请以正规医疗诊断为准,玄学解读不作健康预测。")
    if any(k in question for k in _LEGAL_FIN):
        notes.append("法律/投资类决定请咨询专业人士,玄学不保证具体结果。")
    return {"block": False, "notes": notes}


def soften_output(text):
    flags = []
    for k in _ABSOLUTE:
        if k in text and k not in flags:
            flags.append(k)
            text = text.replace(k, _SOFTEN.get(k, "倾向于"))
    return text, flags


# 常见 LLM 开场白前缀模式，按贪婪程度排列
_PREAMBLE_PREFIXES = [
    "好的，", "好的。", "好的!", "好的 ",
    "没问题，", "没问题。", "没问题 ",
    "请允许我", "我会遵守", "根据您的要求",
]


def strip_preamble(text: str) -> str:
    """如果 LLM 输出了开场白，从第一个 markdown 标题处截断。"""
    for marker in ["### 整体印象", "## 整体印象", "# 整体印象"]:
        idx = text.find(marker)
        if idx >= 0:
            return text[idx:]
    # 如果没有 markdown 标题，尝试去掉常见的确认句首句
    t = text.lstrip()
    for prefix in _PREAMBLE_PREFIXES:
        if t.startswith(prefix):
            # 找到第一个换行或句号后截断
            for sep in ["\n\n", "。\n", "。 "]:
                si = t.find(sep)
                if si > 0:
                    return t[si + len(sep):].lstrip()
            break
    return text
