-- 订阅制业务的维度与事实表（SQLite 语法，PostgreSQL 只需换掉 AUTOINCREMENT）
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id  TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment      TEXT NOT NULL,   -- smb / mid / enterprise
    region       TEXT NOT NULL,   -- north / east / south / west
    signup_date  TEXT NOT NULL    -- YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS dim_plan (
    plan_id            TEXT PRIMARY KEY,
    plan_name          TEXT NOT NULL,
    monthly_price_cents INTEGER NOT NULL CHECK (monthly_price_cents >= 0)
);

CREATE TABLE IF NOT EXISTS f_sub_event (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL REFERENCES dim_customer(customer_id),
    event_date  TEXT NOT NULL,          -- YYYY-MM-DD
    event_type  TEXT NOT NULL CHECK (event_type IN ('new','upgrade','downgrade','churn','reactivate')),
    plan_id     TEXT REFERENCES dim_plan(plan_id)
);

CREATE INDEX IF NOT EXISTS idx_sub_event_customer_date
    ON f_sub_event (customer_id, event_date);

-- 月份骨架：脚本按 --months 生成后写入，SQL 侧不依赖日期函数，方便换库
CREATE TABLE IF NOT EXISTS m_month (
    month      TEXT PRIMARY KEY,        -- YYYY-MM
    month_end  TEXT NOT NULL            -- YYYY-MM-DD
);
