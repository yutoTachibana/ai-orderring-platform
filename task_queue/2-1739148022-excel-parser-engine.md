# Task: Excel解析エンジン

role: core-dev
priority: 2
created_at: 2026-02-10T01:00:00Z

## Description

Create workers/excel_parser.py that parses order specification Excel files using openpyxl. Features: Load column mappings from excel_templates table for flexible parsing. Extract fields: item name, quantity, delivery date, order destination, unit price, remarks. Validate required fields, data types, and master data references. Return structured data as Pydantic models. Handle multiple sheets. Error report with row-level details for invalid data. Write comprehensive tests. Refer to docs/business_process_redesign.md section 3.2 for the expected data fields.
