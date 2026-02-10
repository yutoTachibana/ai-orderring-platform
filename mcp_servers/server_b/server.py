"""WebシステムB向けMCPサーバー (モック)"""
from mcp_servers.common.mcp_base import MockMCPClient


class SystemBServer(MockMCPClient):
    """WebシステムB専用MCPサーバー"""

    def __init__(self):
        super().__init__("system_b")

    def execute_order_input(self, order_data: dict) -> dict:
        """WebシステムBへの発注入力"""
        result = super().execute_order_input(order_data)
        result["system_label"] = "Webシステム B"
        return result
