# Task: レポート自動生成

role: core-dev
priority: 5
created_at: 2026-02-10T01:00:00Z

## Description

Create workers/report_generator.py. Generate weekly/monthly reports. Report types: sales summary (revenue by period/company), project status (active/completed/pipeline), engineer utilization (assigned vs available), invoice aging (overdue analysis), processing pipeline metrics (auto-processed vs manual). Output formats: Excel (openpyxl with charts) and PDF. Schedule management via report_schedules table (cron expressions parsed with croniter). Celery periodic tasks for scheduled reports. API: POST /api/v1/reports/generate (ad-hoc), GET /api/v1/report-schedules (CRUD). Delivery: save to filesystem + Slack notification with file.
