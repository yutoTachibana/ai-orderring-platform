"""Slack承認後にExcel解析結果から実データ（案件・見積・発注）を自動登録するサービス"""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.company import Company, CompanyType
from app.models.project import Project, ProjectStatus, SubcontractingTierLimit
from app.models.quotation import Quotation, QuotationStatus
from app.models.order import Order, OrderStatus
from app.models.automation import ProcessingJob, ProcessingLog
from app.services.tier_eligibility import is_engineer_eligible


# Excel日本語キー → DBフィールドのマッピング
FIELD_MAPPING = {
    # 発注先企業
    "発注先": "company_name",
    "発注先企業": "company_name",
    "クライアント": "company_name",
    "取引先": "company_name",
    "企業名": "company_name",
    # 発注元企業
    "発注元企業": "client_company_name",
    "発注元": "client_company_name",
    # 案件名
    "案件名": "project_name",
    "プロジェクト名": "project_name",
    "件名": "project_name",
    "案件": "project_name",
    # 案件説明
    "案件概要": "project_description",
    "業務内容": "project_description",
    "概要": "project_description",
    "作業内容": "project_description",
    # 開始日
    "開始日": "start_date",
    "契約開始日": "start_date",
    "参画開始日": "start_date",
    "開始": "start_date",
    # 終了日
    "終了日": "end_date",
    "契約終了日": "end_date",
    "参画終了日": "end_date",
    "終了": "end_date",
    # 予算・単価
    "予算": "budget",
    "月額予算": "budget",
    "単価": "unit_price",
    "月額単価": "unit_price",
    "月単価": "unit_price",
    "金額": "unit_price",
    "単価（円/月）": "unit_price",
    # 人数
    "人数": "headcount",
    "必要人数": "headcount",
    "募集人数": "headcount",
    # スキル
    "必須スキル": "required_skills",
    "スキル": "required_skills",
    "言語": "required_skills",
    "技術要件": "required_skills",
    # 備考
    "備考": "notes",
    "特記事項": "notes",
    "その他": "notes",
    # 工数
    "想定工数": "estimated_hours",
    "工数": "estimated_hours",
    "想定稼働時間": "estimated_hours",
    # 精算幅
    "精算幅下限（H）": "min_hours",
    "精算幅上限（H）": "max_hours",
    # 契約形態
    "契約形態": "contract_type",
    # エンジニア
    "エンジニア名": "engineer_name",
    # 勤務地
    "勤務地": "work_location",
    # 担当者
    "担当者": "contact_person",
    # 発注番号
    "発注番号": "external_order_number",
    # 発注日
    "発注日": "order_date",
    # 再委託制限
    "再委託制限": "subcontracting_tier_limit",
    "商流制限": "subcontracting_tier_limit",
    "再委託": "subcontracting_tier_limit",
}


def _parse_date(value: str) -> date | None:
    """日付文字列をパースする。複数フォーマットに対応。"""
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y年%m月%d日",
        "%Y.%m.%d",
    ):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_int(value: str) -> int | None:
    """数値文字列をパースする。カンマや円マーク等を除去。"""
    cleaned = value.replace(",", "").replace("¥", "").replace("円", "").replace("人", "").replace("時間", "").replace("h", "").strip()
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def _normalize_fields(raw: dict[str, str]) -> dict[str, str]:
    """Excel解析結果のキーをDB用フィールド名に正規化する。"""
    normalized = {}
    for key, value in raw.items():
        field_name = FIELD_MAPPING.get(key.strip())
        if field_name and value:
            # 同じフィールドが複数マッチした場合は先勝ち
            if field_name not in normalized:
                normalized[field_name] = value.strip()
    return normalized


def _generate_order_number(db: Session) -> str:
    """発注番号を自動生成する。 ORD-YYYYMMDD-NNN 形式。"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"ORD-{today}-"
    last = (
        db.query(Order)
        .filter(Order.order_number.like(f"{prefix}%"))
        .order_by(Order.order_number.desc())
        .first()
    )
    if last:
        seq = int(last.order_number.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def register_order_from_job(db: Session, job: ProcessingJob) -> dict:
    """
    承認済みジョブのExcel解析結果から案件・見積・発注を自動登録する。

    Returns:
        作成されたレコードの情報を含む辞書
    """
    if not job.result:
        raise ValueError("ジョブに解析結果がありません")

    fields = _normalize_fields(job.result)
    created = {}

    # 1. 企業の取得または作成（発注元企業=クライアント、発注先企業=SES企業）
    # Projectのclient_companyには「発注元企業」を使う
    client_name = fields.get("client_company_name") or fields.get("company_name")
    if client_name:
        company = db.query(Company).filter(Company.name == client_name).first()
        if not company:
            company = Company(
                name=client_name,
                company_type=CompanyType.client,
            )
            db.add(company)
            db.flush()
            created["company"] = {"id": company.id, "name": company.name, "new": True}
        else:
            created["company"] = {"id": company.id, "name": company.name, "new": False}
    else:
        company = db.query(Company).filter(Company.company_type == CompanyType.client).first()
        if not company:
            company = Company(name="未指定", company_type=CompanyType.client)
            db.add(company)
            db.flush()
        created["company"] = {"id": company.id, "name": company.name, "new": False}

    # 2. 案件(Project)の作成
    project_name = fields.get("project_name", f"Slack受注 #{job.id}")
    start_date = _parse_date(fields["start_date"]) if "start_date" in fields else None
    end_date = _parse_date(fields["end_date"]) if "end_date" in fields else None
    budget = _parse_int(fields["budget"]) if "budget" in fields else None
    headcount = _parse_int(fields["headcount"]) if "headcount" in fields else None

    # 再委託制限のマッピング
    tier_limit_raw = fields.get("subcontracting_tier_limit")
    tier_limit = None
    if tier_limit_raw:
        tier_limit_map = {
            "プロパーのみ": SubcontractingTierLimit.proper_only,
            "一社先まで": SubcontractingTierLimit.first_tier,
            "二社先まで": SubcontractingTierLimit.second_tier,
            "制限なし": SubcontractingTierLimit.no_restriction,
            "proper_only": SubcontractingTierLimit.proper_only,
            "first_tier": SubcontractingTierLimit.first_tier,
            "second_tier": SubcontractingTierLimit.second_tier,
            "no_restriction": SubcontractingTierLimit.no_restriction,
        }
        tier_limit = tier_limit_map.get(tier_limit_raw.strip())

    project = Project(
        name=project_name,
        description=fields.get("project_description"),
        client_company_id=company.id,
        status=ProjectStatus.open,
        start_date=start_date,
        end_date=end_date,
        budget=budget,
        required_headcount=headcount,
        subcontracting_tier_limit=tier_limit,
        notes=fields.get("notes"),
    )
    db.add(project)
    db.flush()
    created["project"] = {"id": project.id, "name": project.name}

    # 3. 見積(Quotation)の作成
    # unit_price は月額単価（円/月）、契約期間から合計を算出
    unit_price = _parse_int(fields.get("unit_price", "0")) or 0
    estimated_hours = _parse_int(fields.get("estimated_hours", "160")) or 160
    # 契約月数を計算（開始日〜終了日）
    if start_date and end_date:
        months = max(1, (end_date.year - start_date.year) * 12 + end_date.month - start_date.month)
    else:
        months = 1
    total_amount = unit_price * months if unit_price else (budget or 0)

    # エンジニアの取得: Excel記載の名前で検索、なければ稼働可能な最初のエンジニア
    from app.models.engineer import Engineer
    engineer = None
    engineer_name = fields.get("engineer_name")
    if engineer_name:
        engineer = db.query(Engineer).filter(
            Engineer.full_name == engineer_name,
            Engineer.is_active == True,
        ).first()
    if not engineer:
        # 商流制約を考慮して適格なエンジニアを優先的に割り当て
        candidates = db.query(Engineer).filter(Engineer.is_active == True).all()
        for candidate in candidates:
            if is_engineer_eligible(candidate, project):
                engineer = candidate
                break
        if not engineer and candidates:
            engineer = candidates[0]  # 適格者がいなければ最初のエンジニアをフォールバック
    if not engineer:
        # エンジニアがいない場合はQuotation/Orderは作成しない
        db.add(ProcessingLog(
            job_id=job.id,
            step_name="データ登録",
            status="completed",
            message=f"案件を作成しました（エンジニア未割当のため見積・発注はスキップ）: {project.name}",
        ))
        db.commit()
        created["quotation"] = None
        created["order"] = None
        return created

    quotation = Quotation(
        project_id=project.id,
        engineer_id=engineer.id,
        unit_price=unit_price if unit_price else 500000,
        estimated_hours=estimated_hours,
        total_amount=total_amount if total_amount else 500000 * estimated_hours,
        status=QuotationStatus.approved,
        approved_at=datetime.now(timezone.utc),
        notes=f"Slack受注ジョブ #{job.id} から自動作成",
    )
    db.add(quotation)
    db.flush()
    created["quotation"] = {"id": quotation.id, "total_amount": quotation.total_amount}

    # 4. 発注(Order)の作成
    order_number = _generate_order_number(db)
    order = Order(
        quotation_id=quotation.id,
        order_number=order_number,
        status=OrderStatus.confirmed,
        confirmed_at=datetime.now(timezone.utc),
        notes=f"Slack受注ジョブ #{job.id} から自動作成",
    )
    db.add(order)
    db.flush()
    created["order"] = {"id": order.id, "order_number": order_number}

    # 5. ログ記録
    db.add(ProcessingLog(
        job_id=job.id,
        step_name="データ登録",
        status="completed",
        message=(
            f"自動登録完了: 案件「{project.name}」(ID:{project.id}), "
            f"見積(ID:{quotation.id}), 発注({order_number})"
        ),
    ))
    db.commit()

    return created
