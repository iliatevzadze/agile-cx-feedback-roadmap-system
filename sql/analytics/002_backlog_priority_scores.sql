-- 002_backlog_priority_scores.sql
-- Purpose:
-- Compare CX priority score and RICE score for product backlog decisions.
-- This query demonstrates how support urgency and product prioritization can be viewed together.

SELECT
    bi.backlog_item_id,
    bi.title,
    pa.name AS product_area,
    ft.theme_name,
    bi.status,
    bi.effort_points,
    bi.priority_score AS cx_priority_score,
    bi.rice_score,
    bi.severity_score,
    bi.frequency_score,
    bi.customer_impact_score,
    bi.revenue_impact_score,
    bi.sla_risk_score,
    bi.csat_impact_score,
    bi.churn_risk_score,
    bi.workaround_score,
    ft.frequency_count,
    ft.affected_customers,
    ft.affected_arr,
    ft.avg_csat,
    CASE
        WHEN bi.priority_score >= 75 AND bi.rice_score >= 15 THEN 'Do now: high CX and strong RICE'
        WHEN bi.priority_score >= 75 THEN 'CX escalation priority'
        WHEN bi.rice_score >= 20 THEN 'Efficient product opportunity'
        WHEN bi.priority_score >= 60 THEN 'Plan into upcoming sprint'
        ELSE 'Keep in backlog'
    END AS prioritization_recommendation
FROM backlog_items bi
JOIN feedback_themes ft
    ON bi.theme_id = ft.theme_id
JOIN product_areas pa
    ON bi.product_area_id = pa.product_area_id
ORDER BY
    bi.priority_score DESC,
    bi.rice_score DESC,
    bi.effort_points ASC;
