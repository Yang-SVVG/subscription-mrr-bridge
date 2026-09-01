"""订阅制业务的 MRR 变动桥（bridge）：事件流 -> 月度 MRR -> 五类变动分解。"""

from .bridge import BUCKETS, decompose
from .model import Event, month_end, month_ends, month_key, monthly_mrr

__all__ = [
    "BUCKETS",
    "Event",
    "decompose",
    "month_end",
    "month_ends",
    "month_key",
    "monthly_mrr",
]
