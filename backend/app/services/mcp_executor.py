"""MCPモックサーバー実行サービス: 承認後にWebシステムへの自動入力を実行"""

import sys
import os

from sqlalchemy.orm import Session

from app.models.automation import ProcessingJob, ProcessingLog, RoutingRule

# mcp_servers パッケージへのパスを追加（Docker: /app/mcp_servers、ローカル: 3階層上）
_mcp_parent = os.path.join(os.path.dirname(__file__), "..", "..")  # /app
if _mcp_parent not in sys.path:
    sys.path.insert(0, _mcp_parent)


def determine_target_system(db: Session, order_data: dict) -> str:
    """振り分けルールに基づいてターゲットシステムを判定する。デフォルトは system_a。"""
    rules = (
        db.query(RoutingRule)
        .filter(RoutingRule.is_active.is_(True))
        .order_by(RoutingRule.priority.asc())
        .all()
    )

    for rule in rules:
        ctype = rule.condition_type
        cval = rule.condition_value

        if ctype == "vendor_name" and order_data.get("company_name", "") == cval:
            return rule.target_system.value
        elif ctype == "vendor_name_contains" and cval in order_data.get("company_name", ""):
            return rule.target_system.value
        elif ctype == "category" and order_data.get("project_description", "") == cval:
            return rule.target_system.value
        elif ctype == "keyword" and cval in str(order_data):
            return rule.target_system.value

    return "system_a"


def execute_mcp_input(db: Session, job: ProcessingJob) -> dict:
    """
    MCPモックサーバー経由でWebシステムに発注データを入力する。

    Returns:
        MCP実行結果の辞書
    """
    from mcp_servers.common.mcp_base import MockMCPClient

    # 振り分け判定
    order_data = job.result or {}
    target = determine_target_system(db, order_data)
    job.assigned_system = target

    db.add(ProcessingLog(
        job_id=job.id,
        step_name="振り分け",
        status="completed",
        message=f"振り分け先: {target}",
    ))
    db.flush()

    # MCP実行
    db.add(ProcessingLog(
        job_id=job.id,
        step_name="Web入力",
        status="started",
        message=f"Webシステム入力を開始: {target}",
    ))
    db.flush()

    client = MockMCPClient(target)
    mcp_result = client.execute_order_input(order_data)

    # 結果をjobに保存
    job.result = {**(job.result or {}), "mcp_result": mcp_result}

    db.add(ProcessingLog(
        job_id=job.id,
        step_name="Web入力",
        status="completed",
        message=(
            f"Web入力完了: 確認ID={mcp_result.get('confirmation_id', 'N/A')}, "
            f"システム={mcp_result.get('system', 'N/A')}"
        ),
        screenshot_path=mcp_result.get("screenshot_path"),
    ))
    db.flush()

    return mcp_result
