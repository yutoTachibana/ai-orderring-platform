# Task: 振り分けルールエンジン

role: core-dev
priority: 2
created_at: 2026-02-10T01:00:00Z

## Description

Create workers/routing_engine.py that routes parsed order data to the correct web system (A or B). Features: Load routing rules from routing_rules DB table. Support condition types: exact match, contains, regex, numeric range. Priority-based rule evaluation (first match wins). Fallback to manual routing if no rule matches (create pending_approval job). API endpoints: GET/POST/PUT/DELETE /api/v1/routing-rules for rule management. Rule testing endpoint: POST /api/v1/routing-rules/test (send sample data, return which rule matches). Write tests.
