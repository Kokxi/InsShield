"""险种分类器 — 根据险种名称识别保险大类"""
from typing import Optional


# 分类规则表（按优先级从高到低）
CLASSIFIER_RULES: list[tuple[str, list[str]]] = [
    ("life", ["寿险", "人寿", "终身", "定期寿", "两全", "年金", "万能", "投连", "分红"]),
    ("health", ["健康", "医疗", "重疾", "疾病", "防癌", "护理", "医保"]),
    ("accident", ["意外伤害", "人身意外", "交通意外", "旅游意外", "意外", "驾意"]),
    ("car", ["车险", "机动车", "交强", "三者险", "车损", "商业车险"]),
    ("property", [
        "财产保险", "企财", "家财", "责任保险", "责任险",
        "货运", "工程保险", "保证保险", "信用保险", "农业保险",
    ]),
]

CATEGORY_NAMES = {
    "life": "人寿险",
    "health": "健康险",
    "accident": "意外险",
    "car": "车险",
    "property": "财产险",
    "unknown": "未知",
}


def classify_insurance(policy_type: Optional[str]) -> str:
    """
    根据险种名称识别保险大类。

    按优先级从上到下匹配，先命中归谁。
    返回: life / health / accident / car / property / unknown
    """
    if not policy_type:
        return "unknown"

    text = policy_type.strip()
    for category, keywords in CLASSIFIER_RULES:
        for kw in keywords:
            if kw in text:
                return category
    return "unknown"


def get_category_display_name(category: str) -> str:
    """获取险种分类的中文显示名"""
    return CATEGORY_NAMES.get(category, "未知")
