-- 两条一致性检查：都应当返回空结果

-- 1) 期初 + 新增 + 复活 + 升级 - 降级 - 流失 = 期末
SELECT 'bridge_identity' AS check_name, month, closing_mrr,
       opening_mrr + new_mrr + reactivation_mrr + expansion_mrr
       - contraction_mrr - churn_mrr AS derived_closing
FROM v_bridge_month
WHERE closing_mrr <> opening_mrr + new_mrr + reactivation_mrr + expansion_mrr
                         - contraction_mrr - churn_mrr

UNION ALL

-- 2) 本月期初 = 上月期末（第一个月不检查）
SELECT 'month_continuity' AS check_name, b.month, b.opening_mrr,
       p.closing_mrr AS prev_closing
FROM v_bridge_month b
JOIN v_bridge_month p ON p.month = (
    SELECT MAX(month) FROM m_month WHERE month < b.month
)
WHERE b.opening_mrr <> p.closing_mrr;
