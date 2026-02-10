# Task: 発注・契約管理CRUD API

role: core-dev
priority: 3
created_at: 2026-02-10T00:45:00Z

## Description

Implement CRUD for orders and contracts. Order: created from approved quotation, status (pending→confirmed→cancelled). Contract: linked to order, types (準委任/請負/派遣), period, monthly unit price, working hours (standard 140-180h), status (draft→active→expired→terminated). Both need Pydantic schemas, service layer, pytest tests.
