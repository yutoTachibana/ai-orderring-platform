"""Slack連携: チャネル監視・ファイル受信・通知"""
import os
import tempfile
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.automation import ProcessingJob, SlackChannel, JobStatus


class SlackService:
    """Slack連携サービス (mock対応)"""

    def __init__(self, bot_token: str | None = None):
        self.bot_token = bot_token
        self._client = None

    @property
    def client(self):
        if self._client is None and self.bot_token:
            try:
                from slack_sdk import WebClient
                self._client = WebClient(token=self.bot_token)
            except ImportError:
                self._client = None
        return self._client

    def create_job_from_file(self, channel_id: str, message_id: str, file_path: str) -> int:
        """ファイルからジョブを作成する"""
        db = SessionLocal()
        try:
            job = ProcessingJob(
                slack_message_id=message_id,
                slack_channel_id=channel_id,
                excel_file_path=file_path,
                status=JobStatus.received,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job.id
        finally:
            db.close()

    def send_notification(self, channel_id: str, message: str) -> bool:
        """Slackに通知を送信"""
        if self.client:
            try:
                self.client.chat_postMessage(channel=channel_id, text=message)
                return True
            except Exception:
                return False
        return False

    def send_approval_request(self, channel_id: str, job_id: int, order_summary: str) -> bool:
        """承認リクエストをインタラクティブメッセージで送信"""
        if self.client:
            try:
                self.client.chat_postMessage(
                    channel=channel_id,
                    text=f"承認リクエスト: ジョブ #{job_id}",
                    blocks=[
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"*発注処理の承認リクエスト*\n\nジョブ ID: {job_id}\n{order_summary}"},
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {"type": "button", "text": {"type": "plain_text", "text": "承認"}, "style": "primary", "action_id": f"approve_job_{job_id}"},
                                {"type": "button", "text": {"type": "plain_text", "text": "却下"}, "style": "danger", "action_id": f"reject_job_{job_id}"},
                            ],
                        },
                    ],
                )
                return True
            except Exception:
                return False
        return False
