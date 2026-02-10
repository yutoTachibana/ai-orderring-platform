# Task: DBスキーマ設計とマイグレーション

role: core-dev
priority: 1
created_at: 2026-02-10T00:45:00Z

## Description

Create SQLAlchemy models for all entities defined in CLAUDE.md (User, Company, Engineer, Project, Quotation, Order, Contract, Invoice, SkillTag, MatchingResult). Set up Alembic and create initial migration. Include proper relationships, indexes, and constraints. Status fields should use Enum types matching the transitions in CLAUDE.md. Money fields are integers (JPY). Timestamps are UTC.
