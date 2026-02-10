"""WebシステムA向けMCPサーバー (モック)"""
from mcp_servers.common.mcp_base import MockMCPClient


class SystemAServer(MockMCPClient):
    """WebシステムA専用MCPサーバー"""

    def __init__(self):
        super().__init__("system_a")

    def execute_order_input(self, order_data: dict) -> dict:
        """WebシステムAへの発注入力"""
        result = super().execute_order_input(order_data)
        result["system_label"] = "Webシステム A"
        return result
