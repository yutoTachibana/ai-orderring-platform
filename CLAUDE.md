# ai-orderring-platform

SES業務・システム開発の受発注管理プラットフォーム。
Slack・Excel・複数Webシステムにまたがる手動業務を一元化し、受発注フロー全体をデジタル化・自動化する。

## 背景と目標

現状の課題（docs/cowork_workflow_proposal.md 参照）:
- Excel→Webシステムへの二重入力（2系統）
- 転記ミスのリスク
- ステータス反映の遅延
- 振り分けルール・操作の属人化
- 単純転記に知識労働者の時間を消費

目標（docs/business_process_redesign.md 参照）:
- 処理時間: 15-30分/件 → 1-3分/件（確認のみ）
- 担当者の関与: 100%手動 → 10%（承認・例外対応のみ）
- 転記ミス: 月数件 → ほぼゼロ
- 処理件数: 15-20件/日 → 100件以上/日

## システム全体像

本システムは3層で構成される:

1. **管理プラットフォーム** (本リポジトリのメイン)
   - 管理Excelを置き換えるWebアプリ（案件・要員・契約・請求管理）
   - 受発注ステータスの一元管理とダッシュボード
   - FastAPI + React + PostgreSQL

2. **自動化パイプライン**
   - Slack連携: 発注仕様書（Excel）の自動受信・通知
   - Excel解析エンジン: 添付Excelのパース・バリデーション
   - 振り分けエンジン: 発注先マスタに基づくルールベース振り分け
   - MCPサーバー: Selenium経由でWebシステムA/Bに自動入力

3. **横展開モジュール**
   - 請求書PDF→データ取り込み
   - 週次/月次レポート自動生成
   - 入金消込の照合支援

## Tech Stack

- **Backend**: FastAPI (Python 3.12) + SQLAlchemy 2.0 + Alembic
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS + React Router v7
- **DB**: PostgreSQL 16 + Redis (ジョブキュー)
- **Auth**: JWT (python-jose) + bcrypt
- **API Docs**: FastAPI 自動生成 OpenAPI (Swagger UI)
- **Container**: Docker Compose (backend, frontend, db, redis, mcp-servers)
- **テスト**: pytest (backend), Vitest (frontend)
- **MCP Servers**: Python + Selenium WebDriver (Headless Chrome)
- **Excel処理**: openpyxl
- **Slack連携**: slack-bolt (Python)
- **非同期ジョブ**: Celery + Redis

## ディレクトリ構成

```
backend/
├── app/
│   ├── main.py              # FastAPI アプリケーション
│   ├── config.py            # 設定 (環境変数)
│   ├── database.py          # DB接続・セッション
│   ├── models/              # SQLAlchemy モデル
│   ├── schemas/             # Pydantic スキーマ (リクエスト/レスポンス)
│   ├── routers/             # APIエンドポイント
│   ├── services/            # ビジネスロジック
│   ├── auth/                # 認証・認可
│   └── utils/               # ユーティリティ
├── alembic/                 # マイグレーション
├── tests/                   # テスト
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── components/          # 共通コンポーネント
│   ├── pages/               # ページコンポーネント
│   ├── hooks/               # カスタムフック
│   ├── services/            # API呼び出し
│   ├── types/               # TypeScript型定義
│   ├── utils/               # ユーティリティ
│   └── App.tsx
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile

mcp-servers/
├── server_a/                # WebシステムA向けMCPサーバー
│   ├── server.py            # MCPサーバー本体
│   ├── selenium_driver.py   # Seleniumブラウザ操作
│   ├── page_objects/        # Page Objectパターン
│   └── tests/
├── server_b/                # WebシステムB向けMCPサーバー
│   ├── server.py
│   ├── selenium_driver.py
│   ├── page_objects/
│   └── tests/
└── common/                  # 共通ライブラリ
    ├── mcp_base.py          # MCPサーバー基底クラス
    ├── schema.py            # 入出力スキーマ
    └── screenshot.py        # スクリーンショット管理

workers/
├── slack_listener.py        # Slack受信リスナー (slack-bolt)
├── excel_parser.py          # Excel解析エンジン
├── routing_engine.py        # 振り分けルールエンジン
├── job_processor.py         # Celeryジョブプロセッサ
├── invoice_processor.py     # 請求書PDF取り込み
├── report_generator.py      # レポート自動生成
└── tests/

docker-compose.yml
docs/                        # 既存の業務提案書 (参照用、変更しない)
```

## ドメインモデル

### エンティティ

| エンティティ | テーブル名 | 説明 |
|-------------|-----------|------|
| User | users | システム利用者 (admin/sales/engineer) |
| Company | companies | 取引先企業 (発注元/受注先/SES企業) |
| Engineer | engineers | SESエンジニア (スキル・単価・稼働状況) |
| Project | projects | 開発案件 (案件名・期間・必要スキル・予算) |
| Quotation | quotations | 見積書 (案件に対する見積) |
| Order | orders | 発注 (見積承認→発注) |
| Contract | contracts | 契約 (準委任/請負/派遣、期間、単価) |
| Invoice | invoices | 請求書 (月次、稼働時間ベース) |
| SkillTag | skill_tags | スキルタグマスタ (Java, AWS, PM等) |
| MatchingResult | matching_results | 案件-要員マッチング結果 |
| RoutingRule | routing_rules | 振り分けルールマスタ (条件→Web系統A/B) |
| ExcelTemplate | excel_templates | Excelテンプレート定義 (列マッピング) |
| ProcessingJob | processing_jobs | 自動処理ジョブ (Slack受信→完了まで) |
| ProcessingLog | processing_logs | ジョブ実行ログ (ステップ毎) |
| WebSystemCredential | web_system_credentials | Webシステム認証情報 (暗号化保存) |
| SlackChannel | slack_channels | 監視対象Slackチャネル設定 |
| ReportSchedule | report_schedules | レポート自動生成スケジュール |

### ステータス遷移

```
案件: draft → open → in_progress → completed → closed
見積: draft → submitted → approved → rejected
発注: pending → confirmed → cancelled
契約: draft → active → expired → terminated
請求: draft → sent → paid → overdue
処理ジョブ: received → parsing → routing → pending_approval → executing → completed → failed
```

## 自動化パイプライン

### 処理フロー (docs/business_process_redesign.md に詳細)

```
Slack受信 → Excel解析 → バリデーション → 振り分け判定
  → 担当者に承認依頼 (Slack通知)
  → 承認後: MCP経由でWebシステムA/Bに自動入力
  → 管理DBにステータス・受注番号反映
  → Slack完了通知
```

### 振り分けルール
- routing_rules テーブルに条件を定義 (発注先名、品目カテゴリ等)
- 条件マッチでWebシステムA/Bに自動振り分け
- マッチしない場合は担当者に手動振り分け依頼

### MCPサーバー設計
- 各Webシステム専用のMCPサーバーを構築
- MCP Protocol (stdio) でCowork/本システムから呼び出し可能
- Selenium (Headless Chrome) でブラウザ操作
- Page Objectパターンで画面変更に強い設計
- 入力完了時にスクリーンショットを証跡として保存
- リトライ (最大3回) + エラー時Slack通知

### Excel解析エンジン
- openpyxlでExcelをパース
- excel_templates テーブルで列マッピングを定義 (テンプレート変更に対応)
- バリデーション: 必須項目チェック、データ型チェック、マスタ照合
- エラー行はスキップしてレポート出力

### Slack連携
- slack-bolt で特定チャネルの添付ファイル投稿を監視
- Excel添付を検知 → 自動でパイプライン起動
- 処理結果・エラーをSlackに通知
- 承認リクエストはSlackのインタラクティブメッセージ (ボタン)

## 横展開モジュール

### 請求書PDF取り込み
- PDF請求書をアップロード → テキスト抽出 → データ構造化 → DB登録
- PyMuPDFまたはpdfplumberでPDF解析

### レポート自動生成
- 週次/月次のレポートを自動生成
- report_schedules テーブルでスケジュール定義
- Excel/PDF形式で出力、Slack/メールで配信

### 入金消込
- 入金データ (CSV/Excel) と請求データを照合
- 自動マッチング + 差異レポート

## API設計方針

- RESTful。リソース名は英語複数形 (`/api/v1/projects`, `/api/v1/engineers`)
- 一覧APIはページネーション必須 (`?page=1&per_page=20`)
- フィルタはクエリパラメータ (`?status=open&skill=Python`)
- エラーレスポンスは `{"detail": "message"}` 形式
- 認証が必要なエンドポイントは `Depends(get_current_user)` を使用

## コーディング規約

### Python (Backend)
- フォーマッタ: ruff
- 型ヒント必須
- docstringは主要関数のみ (Google style)
- テストファイルは `tests/test_<module>.py`

### TypeScript (Frontend)
- フォーマッタ: Prettier
- 関数コンポーネントのみ (class不可)
- API呼び出しは `services/` に集約
- ページコンポーネントは `pages/<Entity>/` にまとめる

## セキュリティ要件

- Webシステム認証情報は暗号化してDB保存 (Fernet対称暗号)。環境変数で暗号化キーを管理
- MCPサーバーへの接続はlocalhost限定
- Slack Bot Tokenは環境変数管理
- MCPサーバーは入力完了時のスクリーンショットを保存 (監査証跡)
- 発注データの機密性: アクセスはロールベースで制御

## 重要な注意

- `docs/` ディレクトリは既存の業務提案書。参照のみ、変更しないこと
- `docs/business_process_redesign.md` がTo-Beアーキテクチャの正式仕様。迷ったらこの文書を参照
- 日本語UIが前提。ラベル・メッセージは日本語
- 金額は日本円 (整数、小数点なし)
- 日付はJST表示 (バックエンドはUTC保存)
- MCPサーバーのSeleniumスクリプトはPage Objectパターン必須 (UI変更耐性)
