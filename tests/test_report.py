"""报表渲染的最小契约。"""

from mrrbridge.report import mom_pct, render_markdown, yuan

ROW = {
    "opening_mrr": 100_000,
    "new": 50_000,
    "reactivation": 0,
    "expansion": 10_000,
    "contraction": 0,
    "churn": 0,
    "closing_mrr": 160_000,
    "delta": 60_000,
}


def test_yuan_formats_thousands():
    assert yuan(123_456_700) == "1,234,567"


def test_mom_pct_handles_zero_opening():
    assert mom_pct({"opening_mrr": 0, "delta": 5}) == "—"


def test_render_has_header_and_one_row_per_month():
    table = render_markdown({"2025-01": ROW}, ["2025-01"])
    lines = table.strip().splitlines()
    assert len(lines) == 3                     # 表头 + 分隔 + 一行
    assert "期初 MRR" in lines[0]
    assert lines[2].startswith("| 2025-01 |")
    assert "1,000" in lines[2]                 # 期初 100,000 分 = 1,000 元
    assert "+60.0%" in lines[2]
