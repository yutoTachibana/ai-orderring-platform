# Task: 自動化パイプラインテスト

role: tester
priority: 7
created_at: 2026-02-10T01:00:00Z

## Description

Write comprehensive tests for the automation pipeline. Test Excel parser with various Excel formats (valid, invalid, missing fields, multiple sheets). Test routing engine with various rule configurations. Test job processor with mocked MCP servers. Test Slack listener with mocked slack-bolt. Integration test: full pipeline from Excel upload to job completion. Use pytest fixtures for test data. Create sample Excel files in tests/fixtures/.
