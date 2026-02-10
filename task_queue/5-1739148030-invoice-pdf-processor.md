# Task: 請求書PDF取り込み

role: core-dev
priority: 5
created_at: 2026-02-10T01:00:00Z

## Description

Create workers/invoice_processor.py for PDF invoice processing. Upload PDF → extract text using pdfplumber → parse invoice fields (company name, invoice number, date, items, amounts, tax, total) → validate against existing contracts → create/update Invoice records in DB. API: POST /api/v1/invoices/upload-pdf. Frontend: upload page with drag-and-drop, parsed result preview before saving. Handle multiple invoice formats with configurable extraction rules.
