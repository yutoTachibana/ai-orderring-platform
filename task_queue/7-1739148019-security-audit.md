# Task: セキュリティ監査

role: security
priority: 7
created_at: 2026-02-10T00:45:00Z

## Description

Review the entire codebase for security issues: SQL injection (SQLAlchemy should prevent but verify), XSS (React escaping), CSRF, auth bypass, password storage (bcrypt), JWT token expiration/refresh, input validation, CORS configuration, rate limiting, sensitive data in logs. Report findings and fix critical issues.
