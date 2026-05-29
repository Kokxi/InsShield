"""按险种类型区分统计敏感信息条数"""
from typing import List
from app.models import PolicyResult, SensitiveStats


def compute_stats(results: List[PolicyResult]) -> SensitiveStats:
    """
    从所有识别结果中按险种类型进行统计。

    统计规则：
    - 人身险（life/health/accident）：提取投保人和被保人姓名 → 去重 → 计数
    - 财产险（car/property）：按保单数统计，记录投保人
    - 未知（unknown）：记录数量但不纳入人身险/财产险统计
    """
    life_individual_set: set[str] = set()  # 人身险所有个体（投保人+被保人去重）
    life_insured_set: set[str] = set()     # 人身险被保人（用于 life_insured_list）
    property_applicant_list: list[str] = []
    all_applicant_set: set[str] = set()
    property_count = 0
    unknown_count = 0

    for r in results:
        if r.status != "ok":
            continue

        category = r.fields.insurance_category or "unknown"

        if category in ("life", "health", "accident"):
            # 人身险：投保人 + 被保人 = 涉敏个体
            if r.fields.applicant:
                life_individual_set.add(r.fields.applicant.strip())
                all_applicant_set.add(r.fields.applicant.strip())
            if r.fields.insured:
                text = r.fields.insured.replace(",", "，").replace("、", "，")
                names = [n.strip() for n in text.split("，") if n.strip()]
                life_individual_set.update(names)
                life_insured_set.update(names)

        elif category in ("car", "property"):
            # 财产险：按保单数统计
            property_count += 1
            if r.fields.applicant:
                property_applicant_list.append(r.fields.applicant.strip())
                all_applicant_set.add(r.fields.applicant.strip())

        else:
            # 未知分类
            unknown_count += 1
            if r.fields.applicant:
                all_applicant_set.add(r.fields.applicant.strip())

    return SensitiveStats(
        life_insured_count=len(life_insured_set),
        life_insured_list=sorted(life_insured_set),
        property_count=property_count,
        property_applicant_list=property_applicant_list,
        unknown_count=unknown_count,
        total_applicant_count=len(all_applicant_set),
        total_insured_count=len(life_individual_set),
        sensitive_info_count=len(life_individual_set) + property_count,
    )
