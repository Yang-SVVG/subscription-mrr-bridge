"""事件流 -> 每月月末 MRR 的参考实现（纯标准库，无第三方依赖）。

口径见 docs/methodology.md：
- 一个客户的月末 MRR = 该客户「月末之前最后一次事件」落在的套餐价格；
- 最后一次事件是 churn，则月末 MRR 记为 0（客户流失）；
- 同月多次变更只取最后一次，不逐笔累加。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

#: 会把客户置为「活跃」的事件类型
ACTIVE_TYPES = frozenset({"new", "reactivate", "upgrade", "downgrade"})

#: 客户流失
CHURN = "churn"


@dataclass(frozen=True)
class Event:
    """一条订阅事件。churn 事件没有 plan_id。"""

    customer_id: str
    event_date: date
    event_type: str
    plan_id: Optional[str] = None


def month_key(day: date) -> str:
    """把日期压成 ``YYYY-MM``。"""
    return f"{day.year:04d}-{day.month:02d}"


def month_end(day: date) -> date:
    """所在月的最后一天。"""
    if day.month == 12:
        nxt = date(day.year + 1, 1, 1)
    else:
        nxt = date(day.year, day.month + 1, 1)
    return date.fromordinal(nxt.toordinal() - 1)


def month_ends(start: date, count: int) -> List[date]:
    """从 start 所在月起，连续 count 个月的月末日期。"""
    if count <= 0:
        raise ValueError("count 必须为正整数")
    out: List[date] = []
    year, month = start.year, start.month
    for _ in range(count):
        out.append(month_end(date(year, month, 1)))
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return out


def sort_events(events: Iterable[Event]) -> Dict[str, List[Event]]:
    """按客户分组并按时间排序；同一天内按事件类型排序保证可复现。"""
    grouped: Dict[str, List[Event]] = {}
    for event in events:
        grouped.setdefault(event.customer_id, []).append(event)
    for items in grouped.values():
        items.sort(key=lambda e: (e.event_date, e.event_type))
    return grouped


def monthly_mrr(
    events: Iterable[Event],
    prices: Dict[str, int],
    ends: Sequence[date],
) -> Dict[Tuple[str, str], int]:
    """返回 ``{(month, customer_id): mrr_cents}``，只包含月末 MRR > 0 的客户。"""
    grouped = sort_events(events)
    result: Dict[Tuple[str, str], int] = {}
    for customer_id, items in grouped.items():
        for end in ends:
            last: Optional[Event] = None
            for event in items:
                if event.event_date <= end:
                    last = event
                else:
                    break
            if last is None or last.event_type == CHURN:
                continue
            price = prices.get(last.plan_id or "", 0)
            if price > 0:
                result[(month_key(end), customer_id)] = price
    return result


def first_active_month(monthly: Dict[Tuple[str, str], int]) -> Dict[str, str]:
    """每个客户第一次「月末 MRR > 0」的月份，用来区分新增与复活。"""
    first: Dict[str, str] = {}
    for (month, customer_id) in monthly:
        if customer_id not in first or month < first[customer_id]:
            first[customer_id] = month
    return first
