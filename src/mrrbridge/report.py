"""报表渲染与 SQL 结果比对。"""

from __future__ import annotations

from typing import Dict, List, Mapping, Sequence

from .bridge import BUCKET_LABELS, BUCKETS


def yuan(cents: int) -> str:
    """分 -> 带千分位的元。"""
    sign = "-" if cents < 0 else ""
    return f"{sign}{abs(cents) / 100:,.0f}"


def mom_pct(row: Mapping[str, int]) -> str:
    opening = row["opening_mrr"]
    if opening == 0:
        return "—"
    return f"{row['delta'] / opening * 100:+.1f}%"


def render_markdown(rows: Mapping[str, Mapping[str, int]], months: Sequence[str]) -> str:
    """渲染「按月」的桥式报表（单位：元）。"""
    head = "| 月份 | 期初 MRR | " + " | ".join(BUCKET_LABELS[b] for b in BUCKETS) + " | 期末 MRR | 环比 |"
    sep = "| --- | " + " | ".join(["---:"] * (len(BUCKETS) + 3)) + " |"
    lines = [head, sep]
    for month in months:
        row = rows[month]
        cells = [month, yuan(row["opening_mrr"])]
        cells += [yuan(row[b]) for b in BUCKETS]
        cells += [yuan(row["closing_mrr"]), mom_pct(row)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def sql_rows(conn, months: Sequence[str]) -> Dict[str, Dict[str, int]]:
    """把 ``v_bridge_month`` 读成与 :func:`decompose` 同构的字典。"""
    query = """
        SELECT month, opening_mrr, new_mrr, reactivation_mrr, expansion_mrr,
               contraction_mrr, churn_mrr, closing_mrr
        FROM v_bridge_month
        ORDER BY month
    """
    rows: Dict[str, Dict[str, int]] = {}
    for record in conn.execute(query):
        month = record[0]
        rows[month] = {
            "opening_mrr": record[1],
            "new": record[2],
            "reactivation": record[3],
            "expansion": record[4],
            "contraction": record[5],
            "churn": record[6],
            "closing_mrr": record[7],
            "delta": record[7] - record[1],
        }
    return rows


def compare(python_rows: Mapping[str, Mapping[str, int]], sql_result: Mapping[str, Mapping[str, int]]) -> List[str]:
    """逐月逐桶比对两套实现，返回差异描述（空列表代表完全一致）。"""
    diffs: List[str] = []
    keys = ["opening_mrr", "new", "reactivation", "expansion", "contraction", "churn", "closing_mrr"]
    for month, row in python_rows.items():
        if month not in sql_result:
            diffs.append(f"{month}: SQL 结果缺少该月")
            continue
        for key in keys:
            if row[key] != sql_result[month][key]:
                diffs.append(f"{month}.{key}: python={row[key]} sql={sql_result[month][key]}")
    return diffs
