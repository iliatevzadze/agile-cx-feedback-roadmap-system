-- 001_feedback_theme_summary.sql
-- Purpose:
-- Summarize recurring customer feedback themes by product area.
-- This query shows which customer problems are frequent, high-impact and risky for CX.

SELECT
    ft.theme_id,
    pa.name AS product_area,
    pa.owner_team,
    ft.theme_name,
    ft.frequency_count,
    ft.affected_customers,
    ft.affected_arr,
    ft.avg_csat,
    ft.escalation_count,
    ft.sla_breach_count,
    ft.churn_risk_count,
    bi.priority_score,
    bi.rice_score,
    CASE
        WHEN bi.priority_score >= 75 THEN 'Critical CX priority'
        WHEN bi.priority_score >= 60 THEN 'High CX priority'
        WHEN bi.priority_score >= 45 THEN 'Medium CX priority'
        ELSE 'Monitor'
    END AS cx_priority_bucket
FROM feedback_themes ft
JOIN product_areas pa
    ON ft.product_area_id = pa.product_area_id
LEFT JOIN backlog_items bi
    ON ft.theme_id = bi.theme_id
ORDER BY
    bi.priority_score DESC,
    ft.affected_arr DESC,
    ft.frequency_count DESC;
