# Task: Slack連携 (slack-bolt)

role: core-dev
priority: 2
created_at: 2026-02-10T01:00:00Z

## Description

Create workers/slack_listener.py using slack-bolt for Python. Features: Listen for file_shared events on configured channels (from slack_channels table). Auto-download Excel attachments to a processing directory. Trigger the processing pipeline (Excel parse → routing → approval request). Send interactive messages with approve/reject buttons for human-in-the-loop approval. Send completion notifications with summary. Send error notifications with details. API endpoints for Slack channel management: GET/POST/DELETE /api/v1/slack-channels. Environment variables: SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET. Write tests with mocked Slack client.
