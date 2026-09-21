-- 每个客户每个月末的 MRR（分）。同月多次变更只取最后一次。
DROP VIEW IF EXISTS v_customer_month;

CREATE VIEW v_customer_month AS
WITH last_event AS (
    SELECT m.month,
           c.customer_id,
           (
               SELECT e.event_id
               FROM f_sub_event e
               WHERE e.customer_id = c.customer_id
                 AND e.event_date <= m.month_end
               ORDER BY e.event_date DESC, e.event_id DESC
               LIMIT 1
           ) AS event_id
    FROM m_month m
    CROSS JOIN dim_customer c
)
SELECT l.month,
       l.customer_id,
       COALESCE(
           CASE WHEN e.event_type = 'churn' THEN 0 ELSE p.monthly_price_cents END,
           0
       ) AS mrr_cents
FROM last_event l
LEFT JOIN f_sub_event e ON e.event_id = l.event_id
LEFT JOIN dim_plan p ON p.plan_id = e.plan_id;
