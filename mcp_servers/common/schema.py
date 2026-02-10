"""MCPサーバー共通スキーマ"""
from dataclasses import dataclass, field


@dataclass
class OrderInputRequest:
    vendor_name: str = ""
    order_number: str = ""
    category: str = ""
    description: str = ""
    amount: int = 0
    delivery_date: str = ""
    extra_fields: dict = field(default_factory=dict)


@dataclass
class OrderInputResult:
    success: bool = False
    order_number: str = ""
    confirmation_id: str = ""
    screenshot_path: str | None = None
    error: str | None = None
