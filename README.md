# Agile CX Feedback-to-Roadmap System

A local technical portfolio project that demonstrates how Customer Support, Customer Success and CX Operations feedback can be converted into Agile product backlog items, prioritized roadmap decisions, sprint planning, sprint tracking, sprint reviews and retrospective actions.

## Business Problem

Support teams collect valuable customer pain points every day, but recurring tickets, CSAT comments, escalations, bug reports and feature requests often stay inside support tools. They do not always become structured product backlog items or roadmap decisions.

This project demonstrates an end-to-end workflow:

Support tickets / CSAT comments / feedback
↓
Issue taxonomy and product area mapping
↓
Recurring problem detection
↓
Customer impact scoring
↓
Backlog item creation
↓
User story and acceptance criteria generation
↓
Sprint planning
↓
Sprint board tracking
↓
Sprint review report
↓
Retrospective action items
↓
Measured support impact after release

## Current Milestone

Milestone 1 is focused on:

- Docker Compose PostgreSQL setup
- Environment configuration
- Database schema
- Database connection verification script

## Tech Stack

- Python
- PostgreSQL
- Docker Compose
- SQL
- pytest
- ruff

## Local Setup

1. Copy environment file:

cp .env.example .env

2. Start PostgreSQL:

docker compose up -d

3. Check database connection:

python scripts/db_check.py

4. Apply database schema:

docker compose exec -T postgres psql -U agile_cx_user -d agile_cx_roadmap < sql/001_schema.sql

5. Verify tables:

docker compose exec postgres psql -U agile_cx_user -d agile_cx_roadmap -c "\dt"

## Future Milestones

- Seed data generator
- SQL analytics
- Backlog prioritization engine
- User story generator
- Sprint planning engine
- Sprint review and retrospective reports
- Streamlit dashboard
- Recruiter-facing README polish
