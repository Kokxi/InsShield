"""以人为单位的涉敏统计"""
from typing import List
from app.models import FileResult, GlobalStats


def compute_global_stats(results: List[FileResult]) -> GlobalStats:
    """计算全局统计，含保险大类分支维度和异常检测"""
    stats = GlobalStats()
    unique_names = set()
    anonymous_count = 0

    for r in results:
        if r.status != "ok" or not r.is_insurance_related:
            continue

        stats.total_files += 1
        if r.sensitive_count > 0:
            stats.sensitive_files += 1
        else:
            stats.non_sensitive_files += 1

        # 全局去重人数（按姓名）
        for p in r.persons:
            if p.name:
                unique_names.add(p.name)
            else:
                anonymous_count += 1

        # 分支统计
        branch = r.insurance_branch
        if branch == "life":
            if r.sensitive_count > 0:
                stats.life_sensitive_files += 1
            stats.life_unique_persons += len(r.persons)
        elif branch == "property":
            stats.property_files += 1
            stats.property_sensitive_persons += len(r.persons)

        # 异常文件
        if r.anomaly:
            stats.anomaly_files += 1

    stats.global_unique_persons = len(unique_names) + anonymous_count
    return stats
