# 数据模型

```
dim_customer ──┐
               ├── f_sub_event ── dim_plan
m_month ───────┘
```

| 表 / 视图 | 作用 | 备注 |
| --- | --- | --- |
| `dim_customer` | 客户维度（行业分群、区域、签约日） | 与 CRM 对齐 |
| `dim_plan` | 套餐与月单价（分） | 金额一律用整数分，避免浮点误差 |
| `f_sub_event` | 订阅事件流：new / upgrade / downgrade / churn / reactivate | churn 的 `plan_id` 为空 |
| `m_month` | 月份骨架（月 + 月末日期） | 由脚本写入，SQL 不依赖各库的日期函数 |
| `v_customer_month` | 每个客户每个月末的 MRR | 同月取最后一次事件 |
| `v_bridge_month` | 五类变动的月度汇总 | 与 Python 参考实现逐桶对齐 |

## 为什么用月份骨架表

`v_customer_month` 需要「即使某月没有事件，也要有这一行」。用 `CROSS JOIN m_month` 把网格铺出来，
就不必依赖 `generate_series`（PostgreSQL）或递归 CTE，换库时只改脚本，SQL 不动。

## 为什么 SQL 和 Python 各写一遍

SQL 版给数仓用，Python 版给离线校验和测试用。两边分别实现同一套口径，
再用 `test_sql_vs_python.py` 逐月逐桶对拍 —— 只写一份时，改错了没人发现。
