# Task: 入金消込照合

role: core-dev
priority: 5
created_at: 2026-02-10T01:00:00Z

## Description

Create payment reconciliation feature. Upload bank statement (CSV/Excel) → parse payment records → auto-match against unpaid invoices by amount/company/reference number. Matching strategies: exact amount match, company name fuzzy match, reference number match. API: POST /api/v1/reconciliation/upload, GET /api/v1/reconciliation/{id}/results, POST /api/v1/reconciliation/{id}/confirm. Frontend page: upload, review matches (auto-matched highlighted in green, unmatched in red), manual match/unmatch, confirm all. Auto-update invoice status to 'paid' on confirmation.
