-- 004_release_impact.sql
-- Purpose:
-- Measure post-release CX impact.
-- This query shows whether product fixes reduced tickets, improved CSAT and reduced SLA risk.

SELECT
    ri.release_impact_id,
    bi.backlog_item_id,
    bi.title AS backlog_item,
    pa.name AS product_area,
    ri.before_ticket_volume,
    ri.after_ticket_volume,
    ri.before_ticket_volume - ri.after_ticket_volume AS ticket_volume_reduction,
    ROUND(
        CASE
            WHEN ri.before_ticket_volume = 0 THEN 0
            ELSE (
                (ri.before_ticket_volume - ri.after_ticket_volume)::NUMERIC
                / ri.before_ticket_volume::NUMERIC
            ) * 100
        END,
        2
    ) AS ticket_reduction_percent,
    ri.before_avg_csat,
    ri.after_avg_csat,
    ROUND(ri.after_avg_csat - ri.before_avg_csat, 2) AS csat_change,
    ri.before_sla_breach_rate,
    ri.after_sla_breach_rate,
    ROUND(
        ri.before_sla_breach_rate - ri.after_sla_breach_rate,
        2
    ) AS sla_breach_rate_reduction,
    CASE
        WHEN ri.after_ticket_volume < ri.before_ticket_volume
             AND ri.after_avg_csat > ri.before_avg_csat
             THEN 'Positive support impact'
        WHEN ri.after_ticket_volume < ri.before_ticket_volume
             THEN 'Ticket volume improved'
        ELSE 'Needs more monitoring'
    END AS release_impact_summary,
    ri.measured_at
FROM release_impact ri
JOIN backlog_items bi
    ON ri.backlog_item_id = bi.backlog_item_id
JOIN product_areas pa
    ON ri.product_area_id = pa.product_area_id
ORDER BY
    ticket_reduction_percent DESC,
    csat_change DESC;
