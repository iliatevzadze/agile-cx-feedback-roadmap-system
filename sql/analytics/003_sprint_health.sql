-- 003_sprint_health.sql
-- Purpose:
-- Show sprint commitment, completion, blockers and product areas covered.
-- This query demonstrates Scrum-style sprint tracking and Kanban workflow visibility.

SELECT
    s.sprint_id,
    s.sprint_name,
    s.sprint_goal,
    s.start_date,
    s.end_date,
    s.status,
    s.capacity_points,
    s.committed_points,
    s.completed_points,
    ROUND(
        CASE
            WHEN s.committed_points = 0 THEN 0
            ELSE (s.completed_points::NUMERIC / s.committed_points::NUMERIC) * 100
        END,
        2
    ) AS completion_rate_percent,
    COUNT(si.sprint_item_id) AS sprint_item_count,
    COUNT(si.sprint_item_id) FILTER (WHERE si.status = 'to_do') AS to_do_items,
    COUNT(si.sprint_item_id) FILTER (WHERE si.status = 'in_progress') AS in_progress_items,
    COUNT(si.sprint_item_id) FILTER (WHERE si.status = 'qa') AS qa_items,
    COUNT(si.sprint_item_id) FILTER (WHERE si.status = 'done') AS done_items,
    COUNT(si.sprint_item_id) FILTER (WHERE si.status = 'released') AS released_items,
    COUNT(si.sprint_item_id) FILTER (WHERE si.blocked_flag = TRUE) AS blocked_items,
    COALESCE(SUM(bi.priority_score), 0) AS total_cx_priority_covered,
    COALESCE(SUM(ft.affected_customers), 0) AS affected_customers_covered,
    COALESCE(SUM(ft.affected_arr), 0) AS affected_arr_covered,
    COALESCE(
        STRING_AGG(DISTINCT pa.name, ', ' ORDER BY pa.name),
        'No product areas assigned'
    ) AS product_areas_in_sprint
FROM sprints s
LEFT JOIN sprint_items si
    ON s.sprint_id = si.sprint_id
LEFT JOIN backlog_items bi
    ON si.backlog_item_id = bi.backlog_item_id
LEFT JOIN feedback_themes ft
    ON bi.theme_id = ft.theme_id
LEFT JOIN product_areas pa
    ON bi.product_area_id = pa.product_area_id
GROUP BY
    s.sprint_id,
    s.sprint_name,
    s.sprint_goal,
    s.start_date,
    s.end_date,
    s.status,
    s.capacity_points,
    s.committed_points,
    s.completed_points
ORDER BY
    s.start_date;
