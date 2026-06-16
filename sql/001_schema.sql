CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    plan TEXT NOT NULL,
    arr_value NUMERIC(12, 2) NOT NULL DEFAULT 0,
    health_score INTEGER NOT NULL CHECK (health_score BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_areas (
    product_area_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    owner_team TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_ticket_id TEXT NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    product_area_id BIGINT NOT NULL REFERENCES product_areas(product_area_id) ON DELETE RESTRICT,
    channel TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    first_response_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    csat_score INTEGER CHECK (csat_score BETWEEN 1 AND 5),
    sla_breached BOOLEAN NOT NULL DEFAULT FALSE,
    escalation_flag BOOLEAN NOT NULL DEFAULT FALSE,
    churn_risk_flag BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS feedback_items (
    feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    ticket_id BIGINT REFERENCES support_tickets(ticket_id) ON DELETE SET NULL,
    product_area_id BIGINT NOT NULL REFERENCES product_areas(product_area_id) ON DELETE RESTRICT,
    feedback_type TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    impact_level TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback_themes (
    theme_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_area_id BIGINT NOT NULL REFERENCES product_areas(product_area_id) ON DELETE RESTRICT,
    theme_name TEXT NOT NULL,
    theme_description TEXT NOT NULL,
    frequency_count INTEGER NOT NULL DEFAULT 0,
    avg_csat NUMERIC(4, 2),
    affected_customers INTEGER NOT NULL DEFAULT 0,
    affected_arr NUMERIC(12, 2) NOT NULL DEFAULT 0,
    escalation_count INTEGER NOT NULL DEFAULT 0,
    sla_breach_count INTEGER NOT NULL DEFAULT 0,
    churn_risk_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (product_area_id, theme_name)
);

CREATE TABLE IF NOT EXISTS backlog_items (
    backlog_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    theme_id BIGINT NOT NULL REFERENCES feedback_themes(theme_id) ON DELETE CASCADE,
    product_area_id BIGINT NOT NULL REFERENCES product_areas(product_area_id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    problem_statement TEXT NOT NULL,
    user_story TEXT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    definition_of_ready TEXT NOT NULL,
    definition_of_done TEXT NOT NULL,
    priority_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    severity_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    frequency_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    revenue_impact_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    customer_impact_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    sla_risk_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    csat_impact_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    churn_risk_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    workaround_score NUMERIC(8, 2) NOT NULL DEFAULT 0,
    effort_points INTEGER NOT NULL DEFAULT 1,
    rice_reach NUMERIC(10, 2) NOT NULL DEFAULT 0,
    rice_impact NUMERIC(5, 2) NOT NULL DEFAULT 0,
    rice_confidence NUMERIC(5, 2) NOT NULL DEFAULT 0,
    rice_effort NUMERIC(5, 2) NOT NULL DEFAULT 1,
    rice_score NUMERIC(10, 2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'backlog',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backlog_evidence (
    evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    backlog_item_id BIGINT NOT NULL REFERENCES backlog_items(backlog_item_id) ON DELETE CASCADE,
    ticket_id BIGINT REFERENCES support_tickets(ticket_id) ON DELETE SET NULL,
    feedback_id BIGINT REFERENCES feedback_items(feedback_id) ON DELETE SET NULL,
    evidence_type TEXT NOT NULL,
    evidence_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sprints (
    sprint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sprint_name TEXT NOT NULL UNIQUE,
    sprint_goal TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    capacity_points INTEGER NOT NULL,
    committed_points INTEGER NOT NULL DEFAULT 0,
    completed_points INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'planned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sprint_items (
    sprint_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sprint_id BIGINT NOT NULL REFERENCES sprints(sprint_id) ON DELETE CASCADE,
    backlog_item_id BIGINT NOT NULL REFERENCES backlog_items(backlog_item_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'to_do',
    story_points INTEGER NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    blocked_flag BOOLEAN NOT NULL DEFAULT FALSE,
    blocker_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (sprint_id, backlog_item_id)
);

CREATE TABLE IF NOT EXISTS retro_items (
    retro_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sprint_id BIGINT NOT NULL REFERENCES sprints(sprint_id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    action_owner TEXT,
    action_status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS release_impact (
    release_impact_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    backlog_item_id BIGINT NOT NULL REFERENCES backlog_items(backlog_item_id) ON DELETE CASCADE,
    product_area_id BIGINT NOT NULL REFERENCES product_areas(product_area_id) ON DELETE RESTRICT,
    before_ticket_volume INTEGER NOT NULL,
    after_ticket_volume INTEGER NOT NULL,
    before_avg_csat NUMERIC(4, 2),
    after_avg_csat NUMERIC(4, 2),
    before_sla_breach_rate NUMERIC(5, 2) NOT NULL,
    after_sla_breach_rate NUMERIC(5, 2) NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_support_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_product_area_id ON support_tickets(product_area_id);
CREATE INDEX IF NOT EXISTS idx_feedback_items_customer_id ON feedback_items(customer_id);
CREATE INDEX IF NOT EXISTS idx_feedback_items_product_area_id ON feedback_items(product_area_id);
CREATE INDEX IF NOT EXISTS idx_feedback_themes_product_area_id ON feedback_themes(product_area_id);
CREATE INDEX IF NOT EXISTS idx_backlog_items_priority_score ON backlog_items(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_backlog_items_rice_score ON backlog_items(rice_score DESC);
CREATE INDEX IF NOT EXISTS idx_sprint_items_sprint_id ON sprint_items(sprint_id);

CREATE OR REPLACE VIEW vw_backlog_priority_overview AS
SELECT
    bi.backlog_item_id,
    bi.title,
    pa.name AS product_area,
    ft.theme_name,
    bi.priority_score,
    bi.rice_score,
    bi.effort_points,
    bi.status,
    ft.frequency_count,
    ft.affected_customers,
    ft.affected_arr,
    ft.avg_csat,
    ft.escalation_count,
    ft.sla_breach_count,
    ft.churn_risk_count,
    bi.created_at
FROM backlog_items bi
JOIN feedback_themes ft ON bi.theme_id = ft.theme_id
JOIN product_areas pa ON bi.product_area_id = pa.product_area_id;

CREATE OR REPLACE VIEW vw_sprint_health AS
SELECT
    s.sprint_id,
    s.sprint_name,
    s.sprint_goal,
    s.start_date,
    s.end_date,
    s.capacity_points,
    s.committed_points,
    s.completed_points,
    CASE
        WHEN s.committed_points = 0 THEN 0
        ELSE ROUND((s.completed_points::NUMERIC / s.committed_points::NUMERIC) * 100, 2)
    END AS completion_rate,
    COUNT(si.sprint_item_id) AS total_items,
    COUNT(si.sprint_item_id) FILTER (WHERE si.blocked_flag = TRUE) AS blocked_items,
    s.status
FROM sprints s
LEFT JOIN sprint_items si ON s.sprint_id = si.sprint_id
GROUP BY s.sprint_id;

CREATE OR REPLACE VIEW vw_release_impact_summary AS
SELECT
    ri.release_impact_id,
    bi.title AS backlog_item,
    pa.name AS product_area,
    ri.before_ticket_volume,
    ri.after_ticket_volume,
    ri.before_ticket_volume - ri.after_ticket_volume AS ticket_volume_reduction,
    ri.before_avg_csat,
    ri.after_avg_csat,
    ri.after_avg_csat - ri.before_avg_csat AS csat_change,
    ri.before_sla_breach_rate,
    ri.after_sla_breach_rate,
    ri.before_sla_breach_rate - ri.after_sla_breach_rate AS sla_breach_rate_reduction,
    ri.measured_at
FROM release_impact ri
JOIN backlog_items bi ON ri.backlog_item_id = bi.backlog_item_id
JOIN product_areas pa ON ri.product_area_id = pa.product_area_id;
