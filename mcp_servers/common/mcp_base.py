"""MCPサーバー基底クラスとモッククライアント"""
import uuid
from datetime import datetime


class MCPServerBase:
    """MCPサーバーの基底クラス"""

    def __init__(self, system_name: str):
        self.system_name = system_name

    def execute_order_input(self, order_data: dict) -> dict:
        raise NotImplementedError


class MockMCPClient(MCPServerBase):
    """MCPクライアントのモック実装 (開発・テスト用)"""

    def execute_order_input(self, order_data: dict) -> dict:
        """発注入力をモック実行する"""
        confirmation_id = f"{self.system_name.upper()}-{uuid.uuid4().hex[:8].upper()}"
        order_number = order_data.get("order_number", f"ORD-{uuid.uuid4().hex[:6].upper()}")

        return {
            "success": True,
            "order_number": order_number,
            "confirmation_id": confirmation_id,
            "system": self.system_name,
            "screenshot_path": f"/screenshots/{self.system_name}/{confirmation_id}.png",
            "processed_at": datetime.utcnow().isoformat(),
            "mock": True,
        }
