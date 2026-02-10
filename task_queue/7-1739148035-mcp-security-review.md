# Task: MCPサーバー・自動化セキュリティレビュー

role: security
priority: 7
created_at: 2026-02-10T01:00:00Z

## Description

Security audit of the automation components. Review: credential encryption (Fernet symmetric encryption), MCP server access control (localhost only), Selenium session management (no credential leaking in screenshots), Slack token management, Excel file sanitization (no macro execution), job data access control. Verify screenshots don't contain sensitive data (mask password fields). Ensure processing logs don't leak credentials. Rate limiting on automation APIs.
