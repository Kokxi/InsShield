"""险种分类器 — 根据险种名称识别保险大类"""
from typing import Optional, List


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

# 全文本回退分类关键词（不含"人寿""终身"等公司名高频词，防止"中国人寿"被误判为life）
FALLBACK_CLASSIFIER_RULES: list[tuple[str, list[str]]] = [
    ("car", ["交强", "机动车", "三者险", "车损", "商业车险", "车险"]),
    ("life", ["寿险", "定期寿", "两全", "年金", "万能", "投连", "分红"]),
    ("health", ["医疗", "重疾", "疾病", "防癌", "护理", "健康险", "医保"]),
    ("accident", ["意外伤害", "人身意外", "交通意外", "旅游意外", "驾意"]),
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

CATEGORY_TO_BRANCH: dict[str, str] = {
    "life": "life",
    "health": "life",
    "accident": "life",
    "car": "property",
    "property": "property",
    "social": "social",
    "unknown": "unknown",
}

INSURANCE_BRANCH_DISPLAY: dict[str, str] = {
    "life": "人身保险",
    "property": "财产保险",
    "social": "社会保险",
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


def classify_from_full_text(full_text: str) -> str:
    """根据整段OCR文本识别险种大类（当显式险种字段缺失时的fallback）。

    使用受限关键词集 FALLBACK_CLASSIFIER_RULES，排除"人寿"等公司名常见词，
    防止"中国人寿""平安人寿"等公司名导致误判。
    """
    if not full_text:
        return "unknown"
    for category, keywords in FALLBACK_CLASSIFIER_RULES:
        for kw in keywords:
            if kw in full_text:
                return category
    return "unknown"


def get_category_display_name(category: str) -> str:
    """获取险种分类的中文显示名"""
    return CATEGORY_NAMES.get(category, "未知")


def get_insurance_branch(category: str) -> str:
    """根据险种子类返回保险大类分支。"""
    return CATEGORY_TO_BRANCH.get(category, "unknown")


def get_branch_display(branch: str) -> str:
    """返回保险大类分支的中文显示名。"""
    return INSURANCE_BRANCH_DISPLAY.get(branch, "未知")


def check_anomaly(branch: str, persons: list) -> str:
    """
    检查文件是否存在统计异常。
    财产险中出现多于1个有姓名的人员时，返回 '财产险多人'。
    人身险多人属于正常情况，不标记异常。
    """
    if branch == "property":
        real_persons = [p for p in persons if getattr(p, 'name', '').strip()]
        if len(real_persons) > 1:
            return "财产险多人"
    return ""
