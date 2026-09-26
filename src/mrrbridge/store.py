"""把事件流装进 SQLite，并跑 SQL 侧的视图。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"

SCHEMA_SQL = "01_schema.sql"
SNAPSHOT_SQL = "02_monthly_snapshot.sql"
BRIDGE_SQL = "03_bridge.sql"
CHECKS_SQL = "04_checks.sql"


def run_script(conn: sqlite3.Connection, name: str) -> None:
    """执行 sql/ 下的一个脚本。"""
    conn.executescript((SQL_DIR / name).read_text(encoding="utf-8"))


def insert_all(conn: sqlite3.Connection, customers, events, plans, ends) -> None:
    """写入维度、事件与月份骨架。events 的 plan 为空串时按 NULL 处理。"""
    conn.executemany("INSERT INTO dim_customer VALUES (?,?,?,?,?)", customers)
    conn.executemany(
        "INSERT INTO dim_plan VALUES (?,?,?)",
        [(plan_id, plan_id.title(), price) for plan_id, price in plans.items()],
    )
    conn.executemany(
        "INSERT INTO f_sub_event (customer_id, event_date, event_type, plan_id) VALUES (?,?,?,?)",
        [(cid, day, kind, plan or None) for cid, day, kind, plan in events],
    )
    conn.executemany(
        "INSERT INTO m_month VALUES (?,?)",
        [(f"{end.year:04d}-{end.month:02d}", end.isoformat()) for end in ends],
    )
    conn.commit()


def build(conn: sqlite3.Connection, customers, events, plans, ends) -> None:
    """建表 -> 装数 -> 建月度快照与桥视图。"""
    run_script(conn, SCHEMA_SQL)
    insert_all(conn, customers, events, plans, ends)
    run_script(conn, SNAPSHOT_SQL)
    run_script(conn, BRIDGE_SQL)


def check(conn: sqlite3.Connection) -> list:
    """跑一致性检查，返回违规行（空列表代表通过）。"""
    return list(conn.execute((SQL_DIR / CHECKS_SQL).read_text(encoding="utf-8")))
