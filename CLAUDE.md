# ai-orderring-platform

SES業務・システム開発の受発注管理プラットフォーム。
Slack・Excel・複数Webシステムにまたがる手動業務を一元化し、受発注フロー全体をデジタル化する。

## 背景

現状の課題（docs/ 参照）:
- Excel→Webシステムへの二重入力
- 転記ミスのリスク
- ステータス反映の遅延
- 振り分けルール・操作の属人化

## Tech Stack

- **Backend**: FastAPI (Python 3.12) + SQLAlchemy 2.0 + Alembic
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS + React Router v7
- **DB**: PostgreSQL 16
- **Auth**: JWT (python-jose) + bcrypt
- **API Docs**: FastAPI 自動生成 OpenAPI (Swagger UI)
- **Container**: Docker Compose (backend, frontend, db)
- **テスト**: pytest (backend), Vitest (frontend)

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

### ステータス遷移

```
案件: draft → open → in_progress → completed → closed
見積: draft → submitted → approved → rejected
発注: pending → confirmed → cancelled
契約: draft → active → expired → terminated
請求: draft → sent → paid → overdue
```

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

## 重要な注意

- `docs/` ディレクトリは既存の業務提案書。参照のみ、変更しないこと
- 日本語UIが前提。ラベル・メッセージは日本語
- 金額は日本円 (整数、小数点なし)
- 日付はJST表示 (バックエンドはUTC保存)
