"""五类变动的分类与恒等式。"""

from datetime import date

import pytest

from mrrbridge.bridge import BUCKETS, check_identity, decompose
from mrrbridge.model import Event, month_ends, monthly_mrr

PRICES = {"s": 100_000, "g": 200_000}
ENDS = month_ends(date(2025, 1, 1), 4)          # 2025-01 .. 2025-04
MONTHS = ["2025-01", "2025-02", "2025-03", "2025-04"]


def _events():
    return [
        # A：一直活跃
        Event("A", date(2025, 1, 5), "new", "s"),
        # B：1 月新增 s，2 月升级 g，3 月流失
        Event("B", date(2025, 1, 10), "new", "s"),
        Event("B", date(2025, 2, 3), "upgrade", "g"),
        Event("B", date(2025, 3, 2), "churn"),
        # C：中途进入，算「新增」而不是「复活」
        Event("C", date(2025, 2, 1), "new", "s"),
        # D：1 月新增，2 月流失，4 月复活
        Event("D", date(2025, 1, 1), "new", "s"),
        Event("D", date(2025, 2, 1), "churn"),
        Event("D", date(2025, 4, 1), "reactivate", "s"),
        # E：1 月新增 g，3 月降级到 s
        Event("E", date(2025, 1, 1), "new", "g"),
        Event("E", date(2025, 3, 1), "downgrade", "s"),
        # F：3 月进来当天就降级，月末只按最后一次算
        Event("F", date(2025, 3, 15), "new", "g"),
        Event("F", date(2025, 3, 20), "downgrade", "s"),
    ]


@pytest.fixture()
def rows():
    monthly = monthly_mrr(_events(), PRICES, ENDS)
    return decompose(monthly, ENDS, ["A", "B", "C", "D", "E", "F"])


def test_identity_holds(rows):
    assert check_identity(rows) == []


def test_january_all_new(rows):
    jan = rows["2025-01"]
    assert jan["opening_mrr"] == 0
    assert jan["new"] == 100_000 + 100_000 + 100_000 + 200_000  # A B D E
    assert jan["closing_mrr"] == 500_000


def test_february_new_upgrade_and_churn(rows):
    feb = rows["2025-02"]
    assert feb["opening_mrr"] == 500_000
    assert feb["new"] == 100_000          # C
    assert feb["expansion"] == 100_000    # B 升级
    assert feb["churn"] == 100_000        # D 流失
    assert feb["closing_mrr"] == 600_000


def test_march_contraction_and_same_month_downgrade(rows):
    mar = rows["2025-03"]
    assert mar["churn"] == 200_000        # B
    assert mar["contraction"] == 100_000  # E 降级
    assert mar["new"] == 100_000          # F 按月末的 s 计
    assert mar["closing_mrr"] == 400_000


def test_april_reactivation_not_new(rows):
    apr = rows["2025-04"]
    assert apr["reactivation"] == 100_000
    assert apr["new"] == 0
    assert apr["closing_mrr"] == 500_000


def test_bucket_keys_are_stable(rows):
    for row in rows.values():
        for bucket in BUCKETS:
            assert bucket in row


def test_identity_detects_broken_row():
    broken = {"2025-01": {**{b: 0 for b in BUCKETS}, "opening_mrr": 0, "closing_mrr": 10, "delta": 10}}
    assert check_identity(broken) != []
