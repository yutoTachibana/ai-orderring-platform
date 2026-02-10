# Task: 自動化パイプラインのDBモデル追加

role: core-dev
priority: 1
created_at: 2026-02-10T01:00:00Z

## Description

Add SQLAlchemy models for the automation pipeline entities to the existing models directory: RoutingRule (routing_rules - conditions for routing to WebSystemA/B, fields: name, condition_type, condition_value, target_system, priority), ExcelTemplate (excel_templates - column mapping definitions, fields: name, template_type, column_mappings JSON, validation_rules JSON), ProcessingJob (processing_jobs - end-to-end job tracking, fields: slack_message_id, excel_file_path, status enum [received/parsing/routing/pending_approval/executing/completed/failed], assigned_system, approved_by, approved_at, result JSON), ProcessingLog (processing_logs - step-level logs, fields: job_id FK, step_name, status, message, screenshot_path, created_at), WebSystemCredential (web_system_credentials - encrypted credentials, fields: system_name, username, encrypted_password, login_url, is_active), SlackChannel (slack_channels - monitored channels, fields: channel_id, channel_name, is_active, auto_process), ReportSchedule (report_schedules - schedule definitions, fields: name, report_type, cron_expression, recipients JSON, is_active). Create Alembic migration. Follow existing model patterns in CLAUDE.md.
