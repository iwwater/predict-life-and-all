"""解读层护栏：输入风险话题转介 + 输出绝对化用语软化 + 免责声明。
对齐用户福祉：危机/医疗/法律/财务等不做断言，转介专业。"""
import re

_ABSOLUTE = ["注定", "必然", "一定会", "肯定会", "绝对", "100%", "百分之百", "毫无疑问", "必定"]
_SOFTEN = {"注定": "倾向于", "必然": "较可能", "一定会": "往往会", "肯定会": "多半会",
           "绝对": "通常", "必定": "多半"}
# 风险话题（出现在问题或输出中时附加转介）
_CRISIS = ["自杀", "自残", "轻生", "不想活", "活不下去"]
_MEDICAL = ["重病", "绝症", "癌", "能不能治好", "会不会死", "寿命", "几时死"]
_LEGAL_FIN = ["官司一定", "稳赚", "买哪只股", "全仓", "梭哈", "能不能离婚"]


def check_input(question: str | None) -> dict:
    if not question:
        return {"block": False, "notes": []}
    notes = []
    if any(k in question for k in _CRISIS):
        return {"block": True,
                "message": "听起来你正承受很大的痛苦。这不是算命能回答的问题，"
                           "也请不要独自承受。可以联系当地心理援助热线，或与信任的人/专业人士谈谈。"}
    if any(k in question for k in _MEDICAL):
        notes.append("健康问题请以正规医疗诊断为准，玄学解读不作健康预测。")
    if any(k in question for k in _LEGAL_FIN):
        notes.append("法律/投资类决定请咨询专业人士，玄学不保证具体结果。")
    return {"block": False, "notes": notes}


def soften_output(text: str) -> tuple[str, list[str]]:
    flags = []
    for k in _ABSOLUTE:
        if k in text:
            flags.append(k)
            if k in _SOFTEN:
                text = text.replace(k, _SOFTEN[k])
    return text, flags
