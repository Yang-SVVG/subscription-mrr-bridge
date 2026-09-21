-- 五类变动：新增 / 复活 / 升级 / 降级 / 流失
DROP VIEW IF EXISTS v_bridge_month;

CREATE VIEW v_bridge_month AS
WITH active AS (
    SELECT month, customer_id, mrr_cents
    FROM v_customer_month
    WHERE mrr_cents > 0
),
first_active AS (
    SELECT customer_id, MIN(month) AS first_month
    FROM active
    GROUP BY customer_id
),
grid AS (
    SELECT m.month, c.customer_id
    FROM m_month m
    CROSS JOIN dim_customer c
),
padded AS (
    SELECT g.month,
           g.customer_id,
           COALESCE(a.mrr_cents, 0) AS mrr_cents
    FROM grid g
    LEFT JOIN active a
           ON a.month = g.month AND a.customer_id = g.customer_id
),
shifted AS (
    SELECT month,
           customer_id,
           COALESCE(LAG(mrr_cents) OVER (PARTITION BY customer_id ORDER BY month), 0) AS prev_mrr,
           mrr_cents
    FROM padded
)
SELECT s.month,
       SUM(s.prev_mrr) AS opening_mrr,
       SUM(CASE WHEN s.prev_mrr = 0 AND s.mrr_cents > 0
                 AND f.first_month = s.month THEN s.mrr_cents ELSE 0 END) AS new_mrr,
       SUM(CASE WHEN s.prev_mrr = 0 AND s.mrr_cents > 0
                 AND f.first_month <> s.month THEN s.mrr_cents ELSE 0 END) AS reactivation_mrr,
       SUM(CASE WHEN s.mrr_cents > s.prev_mrr AND s.prev_mrr > 0
                THEN s.mrr_cents - s.prev_mrr ELSE 0 END) AS expansion_mrr,
       SUM(CASE WHEN s.prev_mrr > s.mrr_cents AND s.mrr_cents > 0
                THEN s.prev_mrr - s.mrr_cents ELSE 0 END) AS contraction_mrr,
       SUM(CASE WHEN s.prev_mrr > 0 AND s.mrr_cents = 0
                THEN s.prev_mrr ELSE 0 END) AS churn_mrr,
       SUM(s.mrr_cents) AS closing_mrr
FROM shifted s
LEFT JOIN first_active f ON f.customer_id = s.customer_id
GROUP BY s.month;
