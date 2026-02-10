# Task: 案件-要員マッチングエンジン

role: core-dev
priority: 5
created_at: 2026-02-10T00:45:00Z

## Description

Implement matching logic: given a project's required skills, budget, and period, find available engineers with matching skills. Score by skill match rate, price fit, availability. API: POST /api/v1/matching/search (project_id → ranked engineer list), POST /api/v1/matching/assign (assign engineer to project). Store results in matching_results table.
