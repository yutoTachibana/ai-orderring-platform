"""Tests for /api/v1/slack endpoints."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

import pytest

from app.models.automation import ProcessingJob, ProcessingLog, JobStatus


@pytest.fixture(autouse=True)
def _disable_slack_signing(monkeypatch):
    """Disable Slack signature verification for all tests in this module."""
    from app.config import settings
    monkeypatch.setattr(settings, "SLACK_SIGNING_SECRET", "")


# ---------------------------------------------------------------------------
# POST /api/v1/slack/events
# ---------------------------------------------------------------------------


class TestSlackEvents:
    """Tests for the Slack events endpoint."""

    def test_url_verification_challenge(self, client):
        """url_verification requests should echo back the challenge token."""
        payload = {
            "type": "url_verification",
            "challenge": "test_challenge_token_abc123",
        }
        response = client.post(
            "/api/v1/slack/events",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test_challenge_token_abc123"

    def test_events_without_signature_headers(self, client):
        """When SLACK_SIGNING_SECRET is empty (dev), missing signature headers
        should still pass verification and return 200."""
        payload = {"type": "url_verification", "challenge": "abc"}
        response = client.post(
            "/api/v1/slack/events",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

    def test_events_with_invalid_signature(self, client):
        """With empty SLACK_SIGNING_SECRET the endpoint does not enforce
        signature validation, so an invalid signature should still succeed."""
        payload = {"type": "url_verification", "challenge": "xyz"}
        response = client.post(
            "/api/v1/slack/events",
            content=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "X-Slack-Request-Timestamp": "0",
                "X-Slack-Signature": "v0=invalid_signature",
            },
        )
        assert response.status_code == 200
        assert response.json()["challenge"] == "xyz"

    def test_events_unknown_event_type_returns_ok(self, client):
        """An event type we do not handle should still return {"ok": True}."""
        payload = {
            "type": "event_callback",
            "event": {"type": "app_mention", "text": "hello"},
        }
        response = client.post(
            "/api/v1/slack/events",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    @patch("app.routers.slack._handle_file_shared_event", new_callable=AsyncMock)
    def test_file_shared_event_triggers_handler(self, mock_handler, client):
        """A file_shared event should call _handle_file_shared_event."""
        payload = {
            "type": "event_callback",
            "event": {
                "type": "file_shared",
                "file_id": "F12345",
                "channel_id": "C99999",
            },
        }
        response = client.post(
            "/api/v1/slack/events",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_handler.assert_awaited_once()
        call_args = mock_handler.call_args[0][0]
        assert call_args["file_id"] == "F12345"

    @patch("app.routers.slack._handle_file_shared", new_callable=AsyncMock)
    def test_message_file_share_subtype_triggers_handler(self, mock_handler, client):
        """A message event with subtype=file_share should call _handle_file_shared."""
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "subtype": "file_share",
                "channel": "C11111",
                "ts": "1234567890.123456",
                "files": [{"name": "test.xlsx", "id": "F99"}],
            },
        }
        response = client.post(
            "/api/v1/slack/events",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_handler.assert_awaited_once()


# ---------------------------------------------------------------------------
# POST /api/v1/slack/interactions
# ---------------------------------------------------------------------------


class TestSlackInteractions:
    """Tests for the Slack interactions endpoint."""

    @staticmethod
    def _make_interaction_body(actions, user=None, response_url=""):
        """Helper to build a url-encoded payload like Slack sends."""
        user = user or {"id": "U123", "username": "testuser"}
        payload = json.dumps({
            "type": "block_actions",
            "user": user,
            "channel": {"id": "C99999"},
            "actions": actions,
            "response_url": response_url,
        })
        return urlencode({"payload": payload})

    @patch("app.routers.slack._handle_job_approval", new_callable=AsyncMock)
    def test_approve_job_interaction(self, mock_approval, client, db):
        """An approve_job_ action should trigger job approval."""
        # Create a job in the DB
        job = ProcessingJob(
            status=JobStatus.pending_approval,
            result={"案件名": "Test Project"},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        mock_approval.return_value = "企業: TestCo"

        actions = [{"action_id": f"approve_job_{job.id}"}]
        body = self._make_interaction_body(actions)

        response = client.post(
            "/api/v1/slack/interactions",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_approval.assert_awaited_once_with(job.id, approved=True, slack_user="U123")

    @patch("app.routers.slack._handle_job_approval", new_callable=AsyncMock)
    def test_reject_job_interaction(self, mock_approval, client, db):
        """A reject_job_ action should trigger job rejection."""
        job = ProcessingJob(
            status=JobStatus.pending_approval,
            result={"案件名": "To Be Rejected"},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        mock_approval.return_value = ""

        actions = [{"action_id": f"reject_job_{job.id}"}]
        body = self._make_interaction_body(actions)

        response = client.post(
            "/api/v1/slack/interactions",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        mock_approval.assert_awaited_once_with(job.id, approved=False, slack_user="U123")

    @patch("app.routers.slack._handle_job_approval", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    def test_approve_job_with_response_url(self, mock_httpx_cls, mock_approval, client, db):
        """When response_url is provided, the endpoint should POST to it."""
        job = ProcessingJob(
            status=JobStatus.pending_approval,
            result={"案件名": "Test"},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        mock_approval.return_value = "企業: Acme Corp"

        # Set up the httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_httpx_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        actions = [{"action_id": f"approve_job_{job.id}"}]
        response_url = "https://hooks.slack.com/actions/T00/B00/xxxx"
        body = self._make_interaction_body(actions, response_url=response_url)

        response = client.post(
            "/api/v1/slack/interactions",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        # The mock httpx client should have been used to post to response_url
        mock_client_instance.post.assert_awaited_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == response_url
        posted_json = call_args[1]["json"]
        assert posted_json["replace_original"] is True
        assert "承認" in posted_json["text"]

    @patch("app.routers.slack._handle_job_approval", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    def test_reject_job_with_response_url(self, mock_httpx_cls, mock_approval, client, db):
        """When rejecting with response_url, the message should indicate rejection."""
        job = ProcessingJob(
            status=JobStatus.pending_approval,
            result={"案件名": "Rejected Project"},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        mock_approval.return_value = ""

        mock_client_instance = AsyncMock()
        mock_httpx_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_httpx_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        actions = [{"action_id": f"reject_job_{job.id}"}]
        response_url = "https://hooks.slack.com/actions/T00/B00/yyyy"
        body = self._make_interaction_body(actions, response_url=response_url)

        response = client.post(
            "/api/v1/slack/interactions",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        mock_client_instance.post.assert_awaited_once()
        posted_json = mock_client_instance.post.call_args[1]["json"]
        assert "却下" in posted_json["text"]

    def test_interaction_with_no_actions(self, client):
        """A payload with no actions should return ok without errors."""
        body = self._make_interaction_body(actions=[])
        response = client.post(
            "/api/v1/slack/interactions",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_interaction_with_unknown_action(self, client):
        """An action_id that does not match approve/reject patterns should be ignored."""
        actions = [{"action_id": "unknown_action_123"}]
        body = self._make_interaction_body(actions)
        response = client.post(
            "/api/v1/slack/interactions",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}


# ---------------------------------------------------------------------------
# _handle_job_approval internal function
# ---------------------------------------------------------------------------


class TestHandleJobApproval:
    """Tests for the _handle_job_approval internal function via the
    interactions endpoint, using a real DB (no mocking of _handle_job_approval
    itself). We patch SessionLocal to use the test DB."""

    @staticmethod
    def _make_interaction_body(actions, user=None, response_url=""):
        user = user or {"id": "U123", "username": "approver"}
        payload = json.dumps({
            "type": "block_actions",
            "user": user,
            "channel": {"id": "C99999"},
            "actions": actions,
            "response_url": response_url,
        })
        return urlencode({"payload": payload})

    @patch("app.services.order_registration.register_order_from_job", return_value={})
    @patch("app.services.mcp_executor.execute_mcp_input", return_value={"success": True})
    def test_approve_job_wrong_status_is_noop(self, mock_mcp, mock_reg, client, db):
        """Approving a job that is NOT in pending_approval should be a no-op;
        _handle_job_approval returns '' when job status != pending_approval."""
        job = ProcessingJob(
            status=JobStatus.completed,
            result={"案件名": "Already Done"},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        actions = [{"action_id": f"approve_job_{job.id}"}]
        body = self._make_interaction_body(actions)

        # Patch SessionLocal so _handle_job_approval uses the test DB
        from tests.conftest import TestingSessionLocal
        with patch("app.database.SessionLocal", TestingSessionLocal):
            response = client.post(
                "/api/v1/slack/interactions",
                content=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        assert response.status_code == 200
        # register_order_from_job should NOT have been called
        mock_reg.assert_not_called()

    @patch("app.services.order_registration.register_order_from_job", return_value={})
    @patch("app.services.mcp_executor.execute_mcp_input", return_value={"success": True})
    def test_reject_job_wrong_status_is_noop(self, mock_mcp, mock_reg, client, db):
        """Rejecting a job that is NOT in pending_approval should be a no-op."""
        job = ProcessingJob(
            status=JobStatus.received,
            result={"案件名": "Received Only"},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        actions = [{"action_id": f"reject_job_{job.id}"}]
        body = self._make_interaction_body(actions)

        from tests.conftest import TestingSessionLocal
        with patch("app.database.SessionLocal", TestingSessionLocal):
            response = client.post(
                "/api/v1/slack/interactions",
                content=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        assert response.status_code == 200
        mock_reg.assert_not_called()
