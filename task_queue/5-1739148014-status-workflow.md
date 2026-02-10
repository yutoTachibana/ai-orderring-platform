# Task: ステータス遷移ワークフロー

role: core-dev
priority: 5
created_at: 2026-02-10T00:45:00Z

## Description

Implement strict status transition validation for all entities. Each status change should: validate the transition is allowed, update related entities (e.g. quotation approved → auto-create order), log the transition with timestamp and user. Create a reusable state machine pattern. Add transition history table.
