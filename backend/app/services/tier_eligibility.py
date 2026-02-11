"""商流制約（再委託制限）の判定ロジック"""

from app.models.engineer import Engineer, EmploymentType
from app.models.project import Project, SubcontractingTierLimit


def get_engineer_tier(engineer: Engineer) -> int:
    """エンジニアの商流の深さ（tier）を算出する。

    - proper（自社正社員）→ 0
    - first_tier_proper（一社先プロパー）→ 1
    - freelancer + company_id なし（直接契約フリーランス）→ 1
    - first_tier_freelancer（一社先個人事業主）→ 2
    - freelancer + company_id あり（パートナー企業経由）→ 2
    """
    if engineer.employment_type == EmploymentType.proper:
        return 0
    if engineer.employment_type == EmploymentType.first_tier_proper:
        return 1
    if engineer.employment_type == EmploymentType.first_tier_freelancer:
        return 2
    # freelancer
    if engineer.company_id is not None:
        return 2
    return 1


def is_engineer_eligible(engineer: Engineer, project: Project) -> bool:
    """エンジニアが案件の再委託制限を満たすかどうかを判定する。"""
    limit = project.subcontracting_tier_limit
    if limit is None or limit == SubcontractingTierLimit.no_restriction:
        return True

    tier = get_engineer_tier(engineer)

    if limit == SubcontractingTierLimit.proper_only:
        return tier == 0
    if limit == SubcontractingTierLimit.first_tier:
        return tier <= 1
    if limit == SubcontractingTierLimit.second_tier:
        return tier <= 2

    return True


def validate_engineer_eligibility(engineer: Engineer, project: Project) -> None:
    """エンジニアが案件の再委託制限を満たさない場合に ValueError を送出する。"""
    if is_engineer_eligible(engineer, project):
        return

    tier = get_engineer_tier(engineer)
    limit = project.subcontracting_tier_limit

    tier_labels = {
        0: "プロパー",
        1: "一社先（プロパー/直接契約フリーランス）",
        2: "二社先（パートナー企業経由/一社先個人事業主）",
    }
    limit_labels = {
        SubcontractingTierLimit.proper_only: "プロパーのみ",
        SubcontractingTierLimit.first_tier: "一社先まで",
        SubcontractingTierLimit.second_tier: "二社先まで",
    }

    engineer_label = tier_labels.get(tier, f"tier {tier}")
    limit_label = limit_labels.get(limit, str(limit))

    raise ValueError(
        f"商流制約違反: この案件は「{limit_label}」の制限がありますが、"
        f"エンジニア「{engineer.full_name}」は「{engineer_label}」です"
    )
