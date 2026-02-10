"""振り分けエンジン: ルールベースでWebシステムA/Bに振り分け"""
from sqlalchemy.orm import Session

from app.models.automation import RoutingRule


class RoutingEngine:
    """発注データをルールに基づいてWebシステムに振り分ける"""

    def __init__(self, db: Session):
        self.db = db

    def determine_target(self, order_data: dict) -> str | None:
        """発注データに基づいて対象システムを判定する

        Returns:
            "system_a", "system_b", or None (手動振り分け必要)
        """
        rules = (
            self.db.query(RoutingRule)
            .filter(RoutingRule.is_active.is_(True))
            .order_by(RoutingRule.priority.asc())
            .all()
        )

        for rule in rules:
            if self._evaluate_rule(rule, order_data):
                return rule.target_system.value

        return None

    def _evaluate_rule(self, rule: RoutingRule, data: dict) -> bool:
        """単一ルールを評価する"""
        condition_type = rule.condition_type
        condition_value = rule.condition_value

        if condition_type == "vendor_name":
            return data.get("vendor_name", "") == condition_value
        elif condition_type == "vendor_name_contains":
            return condition_value in data.get("vendor_name", "")
        elif condition_type == "category":
            return data.get("category", "") == condition_value
        elif condition_type == "amount_gte":
            amount = data.get("amount", 0)
            return isinstance(amount, (int, float)) and amount >= float(condition_value)
        elif condition_type == "amount_lt":
            amount = data.get("amount", 0)
            return isinstance(amount, (int, float)) and amount < float(condition_value)
        elif condition_type == "keyword":
            description = data.get("description", "")
            return condition_value in str(description)

        return False
