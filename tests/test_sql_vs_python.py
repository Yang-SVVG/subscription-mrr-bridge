"""SQL 版桥与 Python 参考实现必须逐月逐桶一致。"""

import sqlite3
from datetime import date

import pytest

from gen_events import generate
from mrrbridge.bridge import decompose
from mrrbridge.model import Event, month_ends, month_key, monthly_mrr
from mrrbridge.report import compare, sql_rows
from mrrbridge.store import build, check

START = date(2025, 5, 1)
MONTHS = 10


@pytest.fixture(scope="module")
def both():
    customers, event_rows, plans = generate(customers=200, months=MONTHS, start=START, seed=7)
    ends = month_ends(START, MONTHS)
    months = [month_key(end) for end in ends]

    conn = sqlite3.connect(":memory:")
    build(conn, customers, event_rows, plans, ends)
    sql_side = sql_rows(conn, months)

    events = [Event(cid, date.fromisoformat(day), kind, plan or None) for cid, day, kind, plan in event_rows]
    monthly = monthly_mrr(events, plans, ends)
    py_side = decompose(monthly, ends, [row[0] for row in customers])

    problems = check(conn)
    conn.close()
    return py_side, sql_side, problems


def test_sql_matches_python(both):
    py_side, sql_side, _ = both
    assert compare(py_side, sql_side) == []


def test_checks_pass(both):
    _, _, problems = both
    assert problems == []


def test_identity_over_generated_data(both):
    py_side, _, _ = both
    for row in py_side.values():
        derived = (
            row["opening_mrr"] + row["new"] + row["reactivation"] + row["expansion"]
            - row["contraction"] - row["churn"]
        )
        assert derived == row["closing_mrr"]
