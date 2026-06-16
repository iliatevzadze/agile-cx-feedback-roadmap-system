# Agile CX Feedback-to-Roadmap System

Agile CX Feedback-to-Roadmap System is a business and technical portfolio project that demonstrates how Customer Support, Customer Success and CX Operations data can be converted into structured Agile product execution.

The project simulates a realistic SaaS support environment where customer pain points are collected through support tickets, CSAT scores, SLA breaches, escalations, churn-risk signals and recurring product feedback. Instead of leaving this information inside support tools, the system turns it into product-ready evidence for backlog prioritization, sprint planning and release-impact measurement.

The goal of this project is to show how a CX leader can connect customer-facing operations with Product and Engineering. It demonstrates how support data can be used not only for reporting ticket volume but also for identifying recurring product problems, measuring customer impact, prioritizing roadmap decisions and validating whether shipped improvements actually reduce support burden.

## Business Problem

Support and Customer Success teams often detect product friction before it appears in formal product analytics. They see repeated customer complaints, confusing workflows, bug patterns, billing issues, onboarding gaps, SLA breaches and negative CSAT comments.

However, these insights are often scattered across ticketing systems, spreadsheets, Slack threads and individual team knowledge. Without a structured process, customer feedback may remain reactive and disconnected from product roadmap decisions.

This project solves that problem by creating a repeatable workflow that moves from raw customer feedback to prioritized Agile execution.

## End-to-End Workflow

The system follows this workflow:

```text
Support tickets and CSAT feedback
→ Product area and issue categorization
→ Recurring feedback theme detection
→ Customer impact and SLA risk analysis
→ CX priority scoring
→ RICE prioritization
→ Backlog item generation
→ User story and acceptance criteria creation
→ Sprint planning based on capacity
→ Sprint review and retrospective reporting
→ Release-impact measurement
→ Dashboard and API visibility
```

## What the System Does

The system can answer practical CX and product operations questions such as:

* Which customer issues are recurring most often?
* Which product areas create the highest support burden?
* Which issues affect the most customers?
* Which problems are connected to SLA breaches or escalations?
* Which feedback themes are associated with lower CSAT?
* Which issues represent churn or revenue risk?
* Which problems should be prioritized first?
* How can customer feedback become a clear Agile backlog item?
* How can support evidence become user stories and acceptance criteria?
* How should Product and Engineering plan sprint work from CX evidence?
* Did shipped improvements reduce ticket volume or improve CSAT?

## Business Value

This project demonstrates how a support organization can become a strategic input into product development.

Instead of treating support as a reactive function, the system creates a bridge between Support, Customer Success, Product and Engineering. It helps teams identify the highest-impact customer problems, support prioritization discussions with data and measure whether product changes improve the customer experience.

For a CX, Support or Customer Success manager, this type of workflow can improve roadmap influence, reduce repeated support volume, strengthen cross-functional alignment and make customer feedback more actionable.

## Technical Implementation

The project is built as a local, transparent system using Python, PostgreSQL, Docker Compose, SQL, Streamlit and FastAPI.

It includes:

* PostgreSQL schema for customers, support tickets, feedback themes, backlog items, sprint planning, retrospectives and release impact
* Realistic SaaS seed data generator
* SQL analytics layer for feedback themes, backlog priority, sprint health and release impact
* Backlog prioritization engine using CX priority and RICE scoring
* User story and acceptance criteria generator
* Sprint planning engine based on backlog priority and sprint capacity
* Markdown sprint review and retrospective report generator
* Streamlit dashboard for visual analysis
* FastAPI read API for KPIs, backlog, sprints, release impact and generated reports
* Docker-based local development setup

## Tech Stack

* Python
* PostgreSQL
* Docker Compose
* SQL
* pandas
* Streamlit
* FastAPI
* Uvicorn
* ruff
* pytest

## What This Project Demonstrates

This project demonstrates practical understanding of:

* Customer Support operations
* Customer Success operations
* CX analytics
* SLA and CSAT analysis
* Product feedback loops
* Agile methodology
* Backlog prioritization
* RICE scoring
* User story creation
* Acceptance criteria writing
* Sprint planning
* Sprint review and retrospective reporting
* Release-impact measurement
* PostgreSQL schema design
* SQL reporting
* Python automation
* Dashboard development
* API development
* Local Docker-based development

## Recruiter-Facing Summary

This project shows how I would build a structured operating system for turning customer feedback into product execution.

It combines CX leadership thinking with technical implementation: support tickets become feedback themes, feedback themes become prioritized backlog items, backlog items become user stories, user stories become sprint work and released work is measured through support impact.

The project is designed to demonstrate that I understand both the business side of Customer Support / Customer Success management and the technical systems needed to make support data useful for product and engineering teams.
