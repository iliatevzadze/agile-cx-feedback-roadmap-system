from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from agile_cx_roadmap.dashboard.data import (
    get_backlog_priority,
    get_kpis,
    get_release_impact,
    get_report_files,
    get_sprint_health,
    get_sprint_items,
    get_theme_summary,
    read_report,
)

st.set_page_config(
    page_title="Agile CX Feedback-to-Roadmap Dashboard",
    page_icon="📊",
    layout="wide",
)


def money(value) -> str:
    if value is None or pd.isna(value):
        return "$0.00"
    return f"${float(value):,.2f}"


def number(value) -> str:
    if value is None or pd.isna(value):
        return "0"
    return f"{int(value):,}"


@st.cache_data(ttl=30)
def load_kpis():
    return get_kpis()


@st.cache_data(ttl=30)
def load_theme_summary():
    return get_theme_summary()


@st.cache_data(ttl=30)
def load_backlog_priority():
    return get_backlog_priority()


@st.cache_data(ttl=30)
def load_sprint_health():
    return get_sprint_health()


@st.cache_data(ttl=30)
def load_sprint_items(sprint_id: int | None):
    return get_sprint_items(sprint_id=sprint_id)


@st.cache_data(ttl=30)
def load_release_impact():
    return get_release_impact()


def render_header() -> None:
    st.title("Agile CX Feedback-to-Roadmap Dashboard")
    st.caption(
        "A local portfolio dashboard showing how customer support evidence becomes "
        "prioritized backlog work, Agile sprint planning and post-release impact."
    )


def render_kpis() -> None:
    kpis = load_kpis()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Support Tickets", number(kpis.get("total_tickets")))
    col2.metric("Feedback Themes", number(kpis.get("feedback_themes")))
    col3.metric("Backlog Items", number(kpis.get("backlog_items")))
    col4.metric("Sprints", number(kpis.get("sprints")))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Active Sprints", number(kpis.get("active_sprints")))
    col6.metric("SLA-Breached Tickets", number(kpis.get("sla_breached_tickets")))
    col7.metric("Avg Ticket CSAT", kpis.get("avg_ticket_csat", "0"))
    col8.metric("Affected ARR", money(kpis.get("total_affected_arr")))


def render_theme_tab() -> None:
    st.subheader("Feedback Theme Summary")
    st.write(
        "Recurring customer problems grouped by product area, linked to CX priority "
        "and RICE scoring."
    )

    df = load_theme_summary()

    if df.empty:
        st.info("No feedback themes found.")
        return

    product_areas = ["All", *sorted(df["product_area"].dropna().unique().tolist())]
    selected_area = st.selectbox("Product area", product_areas)

    filtered = df.copy()
    if selected_area != "All":
        filtered = filtered[filtered["product_area"] == selected_area]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    chart_data = (
        filtered.groupby("product_area", as_index=False)["priority_score"]
        .mean()
        .sort_values("priority_score", ascending=False)
    )

    st.subheader("Average CX Priority by Product Area")
    st.bar_chart(chart_data, x="product_area", y="priority_score")


def render_backlog_tab() -> None:
    st.subheader("Prioritized Backlog")
    st.write(
        "Backlog items generated from customer evidence, scored with CX priority "
        "and RICE."
    )

    df = load_backlog_priority()

    if df.empty:
        st.info("No backlog items found.")
        return

    statuses = ["All", *sorted(df["status"].dropna().unique().tolist())]
    selected_status = st.selectbox("Backlog status", statuses)

    min_priority = st.slider(
        "Minimum CX priority",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
    )

    filtered = df[df["priority_score"] >= min_priority].copy()

    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    top_items = filtered.head(10)[["title", "priority_score"]]
    st.subheader("Top Backlog Items by CX Priority")
    st.bar_chart(top_items, x="title", y="priority_score")


def render_sprint_tab() -> None:
    st.subheader("Sprint Health")
    st.write(
        "Sprint capacity, committed points, completion rate and sprint item status."
    )

    sprint_df = load_sprint_health()

    if sprint_df.empty:
        st.info("No sprints found.")
        return

    st.dataframe(sprint_df, use_container_width=True, hide_index=True)

    sprint_options = {
        f"{row.sprint_id} - {row.sprint_name}": int(row.sprint_id)
        for row in sprint_df.itertuples()
    }

    selected_label = st.selectbox(
        "Sprint item detail",
        list(sprint_options.keys()),
    )
    selected_sprint_id = sprint_options[selected_label]

    items_df = load_sprint_items(selected_sprint_id)
    st.subheader("Sprint Items")
    st.dataframe(items_df, use_container_width=True, hide_index=True)

    completion_chart = sprint_df[
        ["sprint_name", "completion_rate_percent"]
    ].sort_values("sprint_name")

    st.subheader("Completion Rate by Sprint")
    st.bar_chart(
        completion_chart,
        x="sprint_name",
        y="completion_rate_percent",
    )


def render_release_tab() -> None:
    st.subheader("Release Impact")
    st.write(
        "Post-release support impact for released backlog items: ticket reduction, "
        "CSAT movement and SLA breach-rate reduction."
    )

    df = load_release_impact()

    if df.empty:
        st.info("No release impact rows found.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)

    chart_data = df[["title", "ticket_reduction_percent"]].head(10)
    st.subheader("Ticket Reduction by Released Item")
    st.bar_chart(chart_data, x="title", y="ticket_reduction_percent")


def render_reports_tab() -> None:
    st.subheader("Generated Sprint Reports")
    st.write(
        "Markdown sprint review and retrospective reports generated by Milestone 7."
    )

    report_files = get_report_files(Path("reports"))

    if not report_files:
        st.info("No report files found. Run scripts/generate_sprint_report.py first.")
        return

    report_options = {path.name: path for path in report_files}
    selected_report = st.selectbox("Report file", list(report_options.keys()))
    selected_path = report_options[selected_report]

    st.caption(f"Path: {selected_path}")
    st.markdown(read_report(selected_path))


def main() -> None:
    render_header()

    with st.sidebar:
        st.header("Dashboard")
        st.write("Local PostgreSQL-powered Agile CX dashboard.")
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

    render_kpis()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Feedback Themes",
            "Backlog Priority",
            "Sprint Health",
            "Release Impact",
            "Reports",
        ]
    )

    with tab1:
        render_theme_tab()

    with tab2:
        render_backlog_tab()

    with tab3:
        render_sprint_tab()

    with tab4:
        render_release_tab()

    with tab5:
        render_reports_tab()


if __name__ == "__main__":
    main()
