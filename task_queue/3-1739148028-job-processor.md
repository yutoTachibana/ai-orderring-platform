# Task: ジョブプロセッサ (Celery)

role: core-dev
priority: 3
created_at: 2026-02-10T01:00:00Z

## Description

Create workers/job_processor.py using Celery with Redis broker. Define async tasks: process_excel_job (full pipeline: parse Excel → route → create ProcessingJob), execute_web_input (call MCP server for a specific job, update status), send_slack_notification (send results to Slack). Job lifecycle: update ProcessingJob status at each step, create ProcessingLog entries. Handle errors gracefully: retry transient failures, mark permanent failures, always notify via Slack. Add Celery worker to docker-compose.yml. Add Redis to docker-compose.yml. API endpoints: GET /api/v1/jobs (list), GET /api/v1/jobs/{id} (detail with logs), POST /api/v1/jobs/{id}/approve, POST /api/v1/jobs/{id}/retry.
