#!/usr/bin/env python
"""端到端：生成数据 -> 落库 -> SQL 桥 -> Python 参考实现 -> 对拍 -> 输出报表。"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "bench"))

from gen_events import generate  # noqa: E402
from mrrbridge.bridge import decompose  # noqa: E402
from mrrbridge.model import Event, month_ends, month_key, monthly_mrr  # noqa: E402
from mrrbridge.report import compare, render_markdown, sql_rows  # noqa: E402
from mrrbridge.store import build, check  # noqa: E402

START = date(2025, 5, 1)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MRR 变动桥：生成 -> 分解 -> 对拍 -> 报表")
    parser.add_argument("--customers", type=int, default=800)
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--last", type=int, default=6, help="报表只打印最近几个月")
    parser.add_argument("--db", default=":memory:", help="落库路径，默认内存库")
    parser.add_argument("--out", default=None, help="把 Markdown 报表写到文件")
    args = parser.parse_args(argv)

    customer_rows, event_rows, plans = generate(customers=args.customers, months=args.months, start=START)
    ends = month_ends(START, args.months)
    months = [month_key(end) for end in ends]
    events = [Event(cid, date.fromisoformat(day), kind, plan or None) for cid, day, kind, plan in event_rows]

    conn = sqlite3.connect(args.db)
    try:
        build(conn, customer_rows, event_rows, plans, ends)
        sql_result = sql_rows(conn, months)

        monthly = monthly_mrr(events, plans, ends)
        python_rows = decompose(monthly, ends, [row[0] for row in customer_rows])

        diffs = compare(python_rows, sql_result)
        if diffs:
            print("SQL 与参考实现不一致：", file=sys.stderr)
            for line in diffs[:10]:
                print("  " + line, file=sys.stderr)
            return 1

        problems = check(conn)
        if problems:
            print("一致性检查未通过：", file=sys.stderr)
            for row in problems:
                print("  ", row, file=sys.stderr)
            return 1

        report = render_markdown(python_rows, months[-args.last :])
        print(f"客户 {len(customer_rows)} / 事件 {len(event_rows)} / 月份 {len(months)}")
        print("SQL 与 Python 对拍一致，一致性检查通过\n")
        print(report)
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report + "\n", encoding="utf-8")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
