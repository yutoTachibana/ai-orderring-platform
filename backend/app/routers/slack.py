import hashlib
import hmac
import time

from fastapi import APIRouter, Request, HTTPException

from app.config import settings

router = APIRouter()


def _verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Slackリクエストの署名を検証する"""
    if not settings.SLACK_SIGNING_SECRET:
        return True  # 開発時にシークレット未設定の場合はスキップ
    if abs(time.time() - int(timestamp)) > 300:
        return False
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    my_signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(my_signature, signature)


@router.post("/events", summary="Slackイベント受信")
async def slack_events(request: Request):
    """Slack Event Subscriptions のエンドポイント"""
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
    signature = request.headers.get("X-Slack-Signature", "")

    if not _verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=403, detail="署名検証に失敗しました")

    import json
    payload = json.loads(body)

    # URL Verification (Slack Appの設定時に送られるチャレンジ)
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    # イベント処理
    event = payload.get("event", {})
    event_type = event.get("type")

    if event_type == "message" and event.get("subtype") == "file_share":
        # ファイル共有イベント → ジョブ作成
        await _handle_file_shared(event)
    elif event_type == "file_shared":
        # file_shared イベント → Slack APIでファイル情報を取得して処理
        await _handle_file_shared_event(event)

    return {"ok": True}


@router.post("/interactions", summary="Slackインタラクション受信")
async def slack_interactions(request: Request):
    """Slack Interactivity (ボタン押下等) のエンドポイント"""
    import json
    from urllib.parse import parse_qs

    body = await request.body()
    parsed = parse_qs(body.decode())
    payload = json.loads(parsed.get("payload", ["{}"])[0])

    actions = payload.get("actions", [])
    user_id = payload.get("user", {}).get("id", "")
    user_name = payload.get("user", {}).get("username", user_id)
    channel_id = payload.get("channel", {}).get("id", "")
    response_url = payload.get("response_url", "")

    import httpx

    for action in actions:
        action_id = action.get("action_id", "")
        if action_id.startswith("approve_job_"):
            job_id = int(action_id.replace("approve_job_", ""))
            result_msg = await _handle_job_approval(job_id, approved=True, slack_user=user_id)
            # 元のメッセージを更新（登録結果も表示）
            if response_url:
                text = f"✅ ジョブ #{job_id} は {user_name} により承認されました。"
                if result_msg:
                    text += f"\n\n📝 *自動登録結果:*\n{result_msg}"
                async with httpx.AsyncClient() as client:
                    await client.post(response_url, json={
                        "replace_original": True,
                        "text": text,
                    })
        elif action_id.startswith("reject_job_"):
            job_id = int(action_id.replace("reject_job_", ""))
            await _handle_job_approval(job_id, approved=False, slack_user=user_id)
            if response_url:
                async with httpx.AsyncClient() as client:
                    await client.post(response_url, json={
                        "replace_original": True,
                        "text": f"❌ ジョブ #{job_id} は {user_name} により却下されました。",
                    })

    return {"ok": True}


async def _handle_file_shared_event(event: dict):
    """file_shared イベントを処理: Slack APIでファイル情報を取得"""
    import httpx

    file_id = event.get("file_id") or event.get("file", {}).get("id")
    channel_id = event.get("channel_id", "")
    if not file_id:
        return

    # Slack APIでファイル情報を取得
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://slack.com/api/files.info",
            headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
            params={"file": file_id},
        )
        data = resp.json()

    if not data.get("ok"):
        print(f"[Slack] files.info failed: {data.get('error')}")
        return

    file_info = data["file"]
    filename = file_info.get("name", "")

    if not filename.endswith((".xlsx", ".xls")):
        return

    # ファイルをダウンロード
    download_url = file_info.get("url_private_download") or file_info.get("url_private")
    if not download_url:
        return

    import os
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            download_url,
            headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
        )
        with open(file_path, "wb") as f:
            f.write(resp.content)

    print(f"[Slack] ファイルダウンロード完了: {filename} -> {file_path}")

    # DBにジョブを作成
    from app.database import SessionLocal
    from app.models.automation import ProcessingJob, ProcessingLog, JobStatus

    db = SessionLocal()
    job = ProcessingJob(
        slack_channel_id=channel_id,
        slack_message_id=event.get("event_ts", ""),
        excel_file_path=file_path,
        status=JobStatus.parsing,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    db.add(ProcessingLog(job_id=job.id, step_name="受信", status="completed", message=f"ファイル受信: {filename}"))
    db.commit()

    # 通知を送信
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
            json={
                "channel": channel_id,
                "text": f"📋 Excel受信: `{filename}`\nジョブ #{job.id} を作成しました。解析を開始します。",
            },
        )

    # Excel解析を実行（ExcelParserで形式を自動判定）
    try:
        from workers.excel_parser import ExcelParser
        parser = ExcelParser()
        result = parser.smart_parse(file_path)

        if isinstance(result, list):
            # テーブル形式（一覧Excel）: 行ごとに個別ジョブを作成
            # 親ジョブは完了扱いにする
            job.result = {"format": "table", "child_count": len(result)}
            job.status = JobStatus.completed
            db.add(ProcessingLog(job_id=job.id, step_name="解析", status="completed", message=f"一覧形式: {len(result)}件を検出、個別ジョブを作成"))
            db.commit()

            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
                    json={
                        "channel": channel_id,
                        "text": f"📋 一覧形式のExcelを検出: {len(result)}件。個別に承認リクエストを送信します。",
                    },
                )

            # 各行を個別ジョブとして作成し、それぞれ承認メッセージを送信
            for i, row in enumerate(result):
                row_data = {k: str(v) for k, v in row.items()}
                child_job = ProcessingJob(
                    slack_channel_id=channel_id,
                    slack_message_id=event.get("event_ts", ""),
                    excel_file_path=file_path,
                    status=JobStatus.pending_approval,
                    result=row_data,
                )
                db.add(child_job)
                db.commit()
                db.refresh(child_job)
                db.add(ProcessingLog(job_id=child_job.id, step_name="解析", status="completed", message=f"一覧 {i+1}/{len(result)}行目"))
                db.commit()

                # 解析内容を表示
                summary = "\n".join(f"  • {k}: {v}" for k, v in list(row_data.items())[:10])
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://slack.com/api/chat.postMessage",
                        headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
                        json={
                            "channel": channel_id,
                            "text": f"✅ ジョブ #{child_job.id} ({i+1}/{len(result)}):\n{summary}",
                            "blocks": [
                                {"type": "section", "text": {"type": "mrkdwn", "text": f"✅ *ジョブ #{child_job.id}* ({i+1}/{len(result)})\n{summary}"}},
                                {"type": "actions", "elements": [
                                    {"type": "button", "text": {"type": "plain_text", "text": "承認"}, "style": "primary", "action_id": f"approve_job_{child_job.id}"},
                                    {"type": "button", "text": {"type": "plain_text", "text": "却下"}, "style": "danger", "action_id": f"reject_job_{child_job.id}"},
                                ]},
                            ],
                        },
                    )
        else:
            # キーバリュー形式（発注仕様書）: 従来通り1ジョブ
            records = {k: str(v) for k, v in result.items()}
            job.result = records
            job.status = JobStatus.pending_approval
            db.add(ProcessingLog(job_id=job.id, step_name="解析", status="completed", message=f"全{len(records)}項目を読み取り"))
            db.commit()

            summary = "\n".join(f"  • {k}: {v}" for k, v in list(records.items())[:10])
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
                    json={
                        "channel": channel_id,
                        "text": f"✅ ジョブ #{job.id} 解析完了:\n{summary}\n\n全{len(records)}項目",
                        "blocks": [
                            {"type": "section", "text": {"type": "mrkdwn", "text": f"✅ *ジョブ #{job.id} 解析完了*\n{summary}\n\n全{len(records)}項目"}},
                            {"type": "actions", "elements": [
                                {"type": "button", "text": {"type": "plain_text", "text": "承認"}, "style": "primary", "action_id": f"approve_job_{job.id}"},
                                {"type": "button", "text": {"type": "plain_text", "text": "却下"}, "style": "danger", "action_id": f"reject_job_{job.id}"},
                            ]},
                        ],
                    },
                )
    except Exception as e:
        job.status = JobStatus.failed
        job.error_message = str(e)
        db.add(ProcessingLog(job_id=job.id, step_name="解析", status="failed", message=str(e)))
        db.commit()
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
                json={
                    "channel": channel_id,
                    "text": f"❌ ジョブ #{job.id} 解析エラー: {e}",
                },
            )
    finally:
        db.close()


async def _handle_file_shared(event: dict):
    """ファイル共有イベントを処理してジョブを作成"""
    from workers.slack_listener import SlackService

    channel_id = event.get("channel", "")
    message_id = event.get("ts", "")
    files = event.get("files", [])

    slack_service = SlackService(settings.SLACK_BOT_TOKEN)

    for file_info in files:
        filename = file_info.get("name", "")
        if filename.endswith((".xlsx", ".xls")):
            # ファイルパスはダウンロード後のパスを設定
            file_path = f"/app/uploads/{filename}"
            job_id = slack_service.create_job_from_file(channel_id, message_id, file_path)
            slack_service.send_notification(
                channel_id,
                f"📋 Excel受信: `{filename}`\nジョブ #{job_id} を作成しました。処理を開始します。",
            )


async def _handle_job_approval(job_id: int, approved: bool, slack_user: str) -> str:
    """ジョブの承認/却下を処理。承認時はExcel解析結果から実データを自動登録する。"""
    from datetime import datetime, timezone
    from app.database import SessionLocal
    from app.models.automation import ProcessingJob, ProcessingLog, JobStatus
    from app.services.order_registration import register_order_from_job
    from app.services.mcp_executor import execute_mcp_input

    db = SessionLocal()
    result_message = ""
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job or job.status != JobStatus.pending_approval:
            return ""

        job.approved_at = datetime.now(timezone.utc)

        if approved:
            job.status = JobStatus.executing
            db.commit()

            try:
                # Step 1: Excel解析結果から実データを自動登録
                created = register_order_from_job(db, job)

                # Step 2: MCPモック経由でWebシステムに自動入力
                mcp_result = execute_mcp_input(db, job)

                job.status = JobStatus.completed
                db.commit()

                # 結果メッセージ作成
                parts = []
                if created.get("company"):
                    c = created["company"]
                    parts.append(f"企業: {c['name']}" + (" (新規)" if c.get("new") else ""))
                if created.get("project"):
                    parts.append(f"案件: {created['project']['name']} (ID:{created['project']['id']})")
                if created.get("quotation"):
                    parts.append(f"見積ID: {created['quotation']['id']}")
                if created.get("order"):
                    parts.append(f"発注: {created['order']['order_number']}")
                # MCP実行結果
                if mcp_result.get("success"):
                    parts.append(f"Web入力: {mcp_result.get('system', 'N/A')} (確認ID: {mcp_result.get('confirmation_id', 'N/A')})")
                result_message = "\n".join(parts)

            except Exception as e:
                job.status = JobStatus.failed
                job.error_message = f"処理エラー: {e}"
                db.add(ProcessingLog(
                    job_id=job.id,
                    step_name="エラー",
                    status="failed",
                    message=str(e),
                ))
                db.commit()
                result_message = f"処理エラー: {e}"
        else:
            job.status = JobStatus.failed
            job.error_message = f"Slackユーザー {slack_user} により却下"
            db.commit()
    finally:
        db.close()

    return result_message
