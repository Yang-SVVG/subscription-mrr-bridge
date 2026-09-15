"""生成可复现的合成订阅事件流（固定 seed，不用第三方库）。

不是真实数据，只用来演示与自测：客户在 18 个月里陆续进入，
每月有小概率升级 / 降级 / 流失，流失客户过一段时间有一定概率复活。
"""

from __future__ import annotations

import random
from datetime import date
from typing import Dict, List, Tuple

PLANS: Dict[str, int] = {
    "starter": 49_900,
    "growth": 129_900,
    "scale": 399_900,
}

PLAN_ORDER = ["starter", "growth", "scale"]

SEGMENTS = ["smb", "mid", "enterprise"]
REGIONS = ["north", "east", "south", "west"]


def month_first_day(year: int, month: int) -> date:
    return date(year, month, 1)


def shift_month(start: date, offset: int) -> date:
    month = start.month - 1 + offset
    return date(start.year + month // 12, month % 12 + 1, 1)


def generate(customers: int = 800, months: int = 18, start: date = date(2025, 5, 1), seed: int = 42):
    """返回 (customers, events, plans)。customers 是 (id, name, segment, region, signup_date)。"""
    rng = random.Random(seed)
    customer_rows: List[Tuple[str, str, str, str, str]] = []
    events: List[Tuple[str, str, str, str]] = []  # (customer_id, date, type, plan_id)

    for index in range(customers):
        customer_id = f"C{index:04d}"
        segment = SEGMENTS[index % len(SEGMENTS)]
        region = REGIONS[index % len(REGIONS)]
        join_index = 0 if index < customers * 0.5 else rng.randrange(months)
        join_day = shift_month(start, join_index)
        join_date = date(join_day.year, join_day.month, rng.randint(1, 20))
        plan_index = 0 if segment == "smb" else (1 if segment == "mid" else 2)
        customer_rows.append(
            (customer_id, f"客户{index:04d}", segment, region, join_date.isoformat())
        )

        plan = PLAN_ORDER[plan_index]
        events.append((customer_id, join_date.isoformat(), "new", plan))
        active = True
        churn_offset = None

        for offset in range(join_index, months):
            if not active:
                # 流失后至少隔一个月才可能复活
                if churn_offset is not None and offset - churn_offset >= 2 and rng.random() < 0.10:
                    day = shift_month(start, offset)
                    events.append(
                        (
                            customer_id,
                            date(day.year, day.month, rng.randint(1, 26)).isoformat(),
                            "reactivate",
                            plan,
                        )
                    )
                    active = True
                    churn_offset = None
                continue

            roll = rng.random()
            day = shift_month(start, offset)
            when = date(day.year, day.month, rng.randint(1, 26)).isoformat()

            if roll < 0.045:
                events.append((customer_id, when, "churn", ""))
                active = False
                churn_offset = offset
            elif roll < 0.095 and plan_index < 2:
                plan_index += 1
                plan = PLAN_ORDER[plan_index]
                events.append((customer_id, when, "upgrade", plan))
            elif roll < 0.135 and plan_index > 0:
                plan_index -= 1
                plan = PLAN_ORDER[plan_index]
                events.append((customer_id, when, "downgrade", plan))

    return customer_rows, events, dict(PLANS)
