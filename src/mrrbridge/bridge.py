"""把月度 MRR 拆成五类变动：新增、复活、升级、降级、流失。"""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from .model import first_active_month, month_key

#: 变动桶的固定顺序，报表按这个顺序输出
BUCKETS = ("new", "reactivation", "expansion", "contraction", "churn")

BUCKET_LABELS = {
    "new": "新增",
    "reactivation": "复活",
    "expansion": "升级",
    "contraction": "降级",
    "churn": "流失",
}


def decompose(
    monthly: Mapping[Tuple[str, str], int],
    ends: Sequence,
    customer_ids: Iterable[str],
) -> Dict[str, Dict[str, int]]:
    """返回 ``{month: {bucket: cents, opening_mrr, closing_mrr, delta, customers_end}}``。

    恒等式：``opening + new + reactivation + expansion - contraction - churn == closing``。
    """
    months = [month_key(end) for end in ends]
    first = first_active_month(dict(monthly))
    customers = list(customer_ids)
    rows: Dict[str, Dict[str, int]] = {}
    previous: Dict[str, int] = {}

    for month in months:
        current = {cid: monthly[(month, cid)] for cid in customers if (month, cid) in monthly}
        row: Dict[str, int] = {bucket: 0 for bucket in BUCKETS}
        row["opening_mrr"] = sum(previous.values())
        row["closing_mrr"] = sum(current.values())
        row["customers_end"] = len(current)

        for customer_id in customers:
            before = previous.get(customer_id, 0)
            after = current.get(customer_id, 0)
            if before == 0 and after > 0:
                bucket = "new" if first.get(customer_id) == month else "reactivation"
                row[bucket] += after
            elif before > 0 and after == 0:
                row["churn"] += before
            elif after > before > 0:
                row["expansion"] += after - before
            elif before > after > 0:
                row["contraction"] += before - after

        row["delta"] = row["closing_mrr"] - row["opening_mrr"]
        rows[month] = row
        previous = current

    return rows


def check_identity(rows: Mapping[str, Mapping[str, int]]) -> List[str]:
    """检查恒等式，返回不成立的月份列表（空列表代表全部通过）。"""
    broken: List[str] = []
    for month, row in rows.items():
        derived = (
            row["opening_mrr"]
            + row["new"]
            + row["reactivation"]
            + row["expansion"]
            - row["contraction"]
            - row["churn"]
        )
        if derived != row["closing_mrr"]:
            broken.append(f"{month}: 推算期末 {derived} != 实际期末 {row['closing_mrr']}")
    return broken
