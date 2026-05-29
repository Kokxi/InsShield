"""按照被保人姓名去重统计敏感信息条数"""
from typing import List
from app.models import PolicyResult, SensitiveStats


def compute_stats(results: List[PolicyResult]) -> SensitiveStats:
    """
    从所有识别结果中提取被保人姓名，去重后统计。
    只有状态为 'ok' 且被保人不为空的才算入统计。
    """
    insured_set: set[str] = set()
    for r in results:
        if r.status == "ok" and r.fields.insured:
            # 按顿号、逗号分割多个被保人
            text = r.fields.insured.replace(",", "，").replace("、", "，")
            names = [n.strip() for n in text.split("，") if n.strip()]
            insured_set.update(names)
    return SensitiveStats(
        total_unique_insured=len(insured_set),
        insured_list=sorted(insured_set),
        details=results,
    )
