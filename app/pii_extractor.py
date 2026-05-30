"""个人信息提取器：正则 + 关键词 + 人员分组"""
import re
from typing import List
from dataclasses import dataclass, field


@dataclass
class PIIItem:
    """单条个人信息"""
    type: str  # id_number / phone / bank_account / address / health / email / birth_date
    value: str
    raw_label: str  # 原文标签，如"联系电话"
    line_number: int  # 在文本中的行号


@dataclass
class Person:
    """一个涉敏个体"""
    name: str
    role: str  # applicant / insured / beneficiary / reporter / anonymous
    details: List[PIIItem] = field(default_factory=list)
    line_number: int = 0  # 姓名出现的行号


# 结构化 PII 正则模式（按优先级从高到低，已匹配的值跳过后续模式）
PII_PATTERNS = [
    ("id_number", r"\b\d{17}[\dXx]\b", "身份证号"),
    ("phone", r"\b1[3-9]\d{9}\b", "手机号"),
    ("bank_account", r"\b\d{16,19}\b", "银行卡号"),
    ("email", r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "邮箱"),
]

# 角色关键词映射（按长度降序，避免子串误匹配）
ROLE_KEYWORDS = [
    ("applicant", ["投保人", "申请人"]),
    ("insured", ["被保险人", "被保人"]),
    ("beneficiary", ["受益人"]),
    ("reporter", ["报案人", "出险人"]),
]

# 地址关键词（仅限个人地址，不含"公司地址""单位地址"等营业地址）
ADDRESS_KEYWORDS = ["联系地址", "住址", "住所"]

# 健康信息关键词（仅限个人健康状况，不含保险产品中的"疾病""住院"等保险责任术语）
HEALTH_KEYWORDS = ["既往病史", "健康状况"]

# 出生日期关键词（按长度降序）
BIRTH_KEYWORDS = ["出生日期", "出生年月", "生日"]

# 姓名过滤黑名单（OCR 误提取为姓名的常见非姓名词）
NAME_BLACKLIST = [
    "请仔细阅读", "特别重要", "特别提示", "以及", "条款",
    "注意", "重要提示", "保险条款", "被保险人条款", "投保人条款",
    "与投保人", "和被保险人", "或受益人", "同一",
    # 常见中文非姓名 2 字词
    "义务", "责任", "免责", "全部", "部分", "特别", "重要",
    "提示", "保险", "合同", "约定", "按照", "规定", "但是",
]


def _dedup_pii(items: List[PIIItem]) -> List[PIIItem]:
    """去重 PII：同一行相同值的只保留第一个"""
    seen = set()
    result = []
    for item in items:
        key = (item.line_number, item.value)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _is_valid_name(name: str) -> bool:
    """验证是否为有效的中文姓名"""
    # 长度 2~4 个汉字
    if not re.fullmatch(r'[一-鿿]{2,4}', name):
        return False
    # 不在黑名单中
    for black in NAME_BLACKLIST:
        if black in name:
            return False
    return True


def extract_pii_from_text(text: str) -> List[PIIItem]:
    """从文本中提取结构化 PII（正则匹配），已匹配的值不会重复提取"""
    items = []
    # 记录每行已匹配的值，避免同一值被多个模式匹配（如身份证号被误认作银行卡号）
    matched_values_per_line: dict[int, set[str]] = {}

    lines = text.split('\n')
    for line_no, line in enumerate(lines):
        if line_no not in matched_values_per_line:
            matched_values_per_line[line_no] = set()

        for pii_type, pattern, label in PII_PATTERNS:
            matches = re.finditer(pattern, line)
            for m in matches:
                value = m.group()
                # 跳过已被前一模式匹配的值（如身份证号被id_number匹配后，不再作为bank_account）
                if value in matched_values_per_line[line_no]:
                    continue
                items.append(PIIItem(pii_type, value, label, line_no))
                matched_values_per_line[line_no].add(value)

    return items


def extract_persons(text: str) -> List[Person]:
    """提取所有 Person（姓名 + 角色）"""
    persons = []
    lines = text.split('\n')

    for line_no, line in enumerate(lines):
        for role, keywords in ROLE_KEYWORDS:
            for kw in keywords:
                if kw in line:
                    idx = line.find(kw)
                    remaining = line[idx + len(kw):].lstrip("：: ")
                    if remaining:
                        # 用正则取第一个连续中文字段
                        import re
                        match = re.match(r'[一-鿿]+', remaining)
                        if match:
                            name = match.group(0)
                            if _is_valid_name(name):
                                persons.append(Person(name, role, [], line_no))
    return persons


def group_pii_to_persons(persons: List[Person], pii_items: List[PIIItem],
                         text: str, max_distance: int = 5) -> List[Person]:
    """将 PII 按文本位置就近归属到最近的 Person"""
    # 先对 PII 去重
    pii_items = _dedup_pii(pii_items)

    lines = text.split('\n')

    # 提取地址、健康信息、出生日期（按关键词，同类关键词每行只匹配第一个）
    for line_no, line in enumerate(lines):
        # 地址
        addr_found = False
        for kw in ADDRESS_KEYWORDS:
            if addr_found:
                break
            if kw in line:
                idx = line.find(kw)
                addr = line[idx + len(kw):].lstrip("：: ").strip()
                if addr:
                    pii_items.append(PIIItem("address", addr, kw, line_no))
                    addr_found = True

        # 健康信息
        health_found = False
        for kw in HEALTH_KEYWORDS:
            if health_found:
                break
            if kw in line:
                pii_items.append(PIIItem("health", line.strip(), kw, line_no))
                health_found = True

        # 出生日期
        birth_found = False
        for kw in BIRTH_KEYWORDS:
            if birth_found:
                break
            if kw in line:
                idx = line.find(kw)
                remaining = line[idx + len(kw):].lstrip("：: ").strip()
                if remaining:
                    pii_items.append(PIIItem("birth_date", remaining, kw, line_no))
                    birth_found = True

    # 归属 PII 到 Person
    for pii in pii_items:
        if not persons:
            persons.append(Person("", "anonymous", [pii], pii.line_number))
            continue

        # 找距离最近的 Person
        min_dist = float('inf')
        closest = None
        for p in persons:
            dist = abs(pii.line_number - p.line_number)
            if dist < min_dist:
                min_dist = dist
                closest = p

        if min_dist <= max_distance:
            closest.details.append(pii)
        else:
            persons.append(Person("", "anonymous", [pii], pii.line_number))

    return persons
