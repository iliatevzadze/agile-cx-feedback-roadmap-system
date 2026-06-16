-- 005_customer_evidence_by_backlog_item.sql
-- Purpose:
-- Show linked support/customer evidence behind each backlog item.
-- This demonstrates that roadmap decisions are grounded in real customer pain.

WITH evidence_context AS (
    SELECT
        be.backlog_item_id,
        be.evidence_type,
        be.evidence_text,
        COALESCE(st.ticket_id, fi.ticket_id) AS ticket_id,
        COALESCE(st.customer_id, fi.customer_id) AS customer_id,
        COALESCE(st.csat_score, NULL) AS ticket_csat_score,
        COALESCE(st.sla_breached, FALSE) AS sla_breached,
        COALESCE(st.escalation_flag, FALSE) AS escalation_flag,
        COALESCE(st.churn_risk_flag, FALSE) AS churn_risk_flag
    FROM backlog_evidence be
    LEFT JOIN support_tickets st
        ON be.ticket_id = st.ticket_id
    LEFT JOIN feedback_items fi
        ON be.feedback_id = fi.feedback_id
)

SELECT
    bi.backlog_item_id,
    bi.title,
    pa.name AS product_area,
    ft.theme_name,
    bi.priority_score,
    bi.rice_score,
    COUNT(ec.evidence_type) AS linked_evidence_count,
    COUNT(DISTINCT ec.ticket_id) AS linked_ticket_count,
    COUNT(DISTINCT ec.customer_id) AS affected_customers_with_evidence,
    ROUND(AVG(ec.ticket_csat_score), 2) AS avg_linked_ticket_csat,
    COUNT(*) FILTER (WHERE ec.sla_breached = TRUE) AS linked_sla_breaches,
    COUNT(*) FILTER (WHERE ec.escalation_flag = TRUE) AS linked_escalations,
    COUNT(*) FILTER (WHERE ec.churn_risk_flag = TRUE) AS linked_churn_risk_flags,
    STRING_AGG(
        DISTINCT c.company_name,
        '; '
        ORDER BY c.company_name
    ) AS example_customers,
    STRING_AGG(
        DISTINCT LEFT(ec.evidence_text, 120),
        ' | '
        ORDER BY LEFT(ec.evidence_text, 120)
    ) AS evidence_examples
FROM backlog_items bi
JOIN feedback_themes ft
    ON bi.theme_id = ft.theme_id
JOIN product_areas pa
    ON bi.product_area_id = pa.product_area_id
LEFT JOIN evidence_context ec
    ON bi.backlog_item_id = ec.backlog_item_id
LEFT JOIN customers c
    ON ec.customer_id = c.customer_id
GROUP BY
    bi.backlog_item_id,
    bi.title,
    pa.name,
    ft.theme_name,
    bi.priority_score,
    bi.rice_score
ORDER BY
    bi.priority_score DESC,
    linked_evidence_count DESC;
