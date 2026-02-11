# AI受発注プラットフォーム システム仕様書

## 1. システム概要

SES（システムエンジニアリングサービス）業務における受発注管理を一元化するWebアプリケーション。
Slack・Excel・複数Webシステムにまたがる手動業務をデジタル化し、受発注フロー全体を自動化する。

### 目標指標

| 指標 | Before | After |
|------|--------|-------|
| 処理時間/件 | 15-30分 | 1-3分（確認のみ） |
| 担当者の関与 | 100%手動 | 10%（承認・例外対応のみ） |
| 転記ミス | 月数件 | ほぼゼロ |
| 処理件数/日 | 15-20件 | 100件以上 |

---

## 2. システムアーキテクチャ

```mermaid
graph TB
    subgraph External["外部システム"]
        Slack[Slack<br/>ファイル共有・承認]
        WebA[Webシステム A]
        WebB[Webシステム B]
        Bank[銀行<br/>入金CSV]
    end

    subgraph Frontend["フロントエンド (React + Vite)"]
        Browser[ブラウザ<br/>localhost:5173]
    end

    subgraph Backend["バックエンド (FastAPI)"]
        API[FastAPI<br/>localhost:8000]
        Auth[JWT認証]
        Routers[APIルーター x 13]
        Services[ビジネスロジック]
    end

    subgraph Workers["非同期ワーカー"]
        Celery[Celery Worker]
        Beat[Celery Beat<br/>定期実行]
        ExcelParser[Excel解析エンジン]
        MCPExec[MCP実行エンジン]
    end

    subgraph DataStores["データストア"]
        PG[(PostgreSQL 16)]
        Redis[(Redis 7<br/>ジョブキュー)]
    end

    Browser -->|HTTP/REST| API
    Slack -->|Webhook| API
    API --> Auth
    Auth --> Routers
    Routers --> Services
    Services --> PG
    API --> Redis
    Celery --> Redis
    Celery --> PG
    Celery --> ExcelParser
    Celery --> MCPExec
    Beat --> Redis
    MCPExec -->|Selenium| WebA
    MCPExec -->|Selenium| WebB
    Bank -->|CSV Import| API
```

### テックスタック

| レイヤー | 技術 |
|----------|------|
| フロントエンド | React 18, TypeScript, Vite, TailwindCSS, React Router v7 |
| バックエンド | FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic |
| DB | PostgreSQL 16 |
| キャッシュ/キュー | Redis 7 |
| 認証 | JWT (python-jose) + bcrypt |
| 非同期ジョブ | Celery + Redis |
| Excel処理 | openpyxl |
| Slack連携 | slack-bolt / slack-sdk |
| MCP/ブラウザ自動操作 | Selenium WebDriver (Headless Chrome) |
| コンテナ | Docker Compose |

---

## 3. データモデル (ER図)

```mermaid
erDiagram
    User {
        int id PK
        string email UK
        string hashed_password
        string full_name
        enum role "admin / sales / engineer"
        bool is_active
    }

    Company {
        int id PK
        string name
        enum company_type "client / vendor / ses"
        string address
        string phone
        string email
        string website
        string notes
        bool is_active
    }

    Engineer {
        int id PK
        string full_name
        string email
        string phone
        int company_id FK
        enum employment_type "proper / first_tier_proper / freelancer / first_tier_freelancer"
        int hourly_rate
        int monthly_rate
        enum availability_status "available / assigned / unavailable"
        int years_of_experience
        string notes
        bool is_active
    }

    SkillTag {
        int id PK
        string name UK
        enum category "language / framework / cloud / other"
    }

    Project {
        int id PK
        string name
        string description
        int client_company_id FK
        enum status "draft / open / in_progress / completed / closed"
        enum subcontracting_tier_limit "proper_only / first_tier / second_tier / no_restriction"
        date start_date
        date end_date
        int budget
        int required_headcount
        string notes
    }

    Quotation {
        int id PK
        int project_id FK
        int engineer_id FK
        int unit_price
        int estimated_hours
        int total_amount
        enum status "draft / submitted / approved / rejected"
        datetime submitted_at
        datetime approved_at
        string notes
    }

    Order {
        int id PK
        int quotation_id FK
        string order_number UK
        enum status "pending / confirmed / cancelled"
        datetime confirmed_at
        string notes
    }

    Contract {
        int id PK
        int order_id FK
        string contract_number UK
        enum contract_type "quasi_delegation / contract / dispatch"
        int engineer_id FK
        int project_id FK
        date start_date
        date end_date
        int monthly_rate
        int min_hours
        int max_hours
        enum status "draft / active / expired / terminated"
        string notes
    }

    Invoice {
        int id PK
        int contract_id FK
        string invoice_number UK
        string billing_month
        float working_hours
        int base_amount
        int adjustment_amount
        int tax_amount
        int total_amount
        enum status "draft / sent / paid / overdue"
        datetime sent_at
        datetime paid_at
        string notes
    }

    Payment {
        int id PK
        int invoice_id FK
        date payment_date
        int amount
        string payer_name
        string reference_number
        string bank_name
        enum status "unmatched / matched / confirmed"
        string notes
    }

    MatchingResult {
        int id PK
        int project_id FK
        int engineer_id FK
        float score
        float skill_match_rate
        bool rate_match
        bool availability_match
        bool tier_eligible
    }

    ProcessingJob {
        int id PK
        string slack_message_id
        string slack_channel_id
        string excel_file_path
        enum status "received / parsing / routing / pending_approval / executing / completed / failed"
        string assigned_system
        int approved_by FK
        json result
        string error_message
    }

    ProcessingLog {
        int id PK
        int job_id FK
        string step_name
        string status
        string message
        string screenshot_path
    }

    RoutingRule {
        int id PK
        string name
        enum condition_type "vendor_name / vendor_name_contains / category / keyword"
        string condition_value
        enum target_system "system_a / system_b"
        int priority
        bool is_active
    }

    Company ||--o{ Engineer : "所属"
    Company ||--o{ Project : "クライアント"
    Engineer }o--o{ SkillTag : "スキル"
    Project }o--o{ SkillTag : "必須スキル"
    Project ||--o{ Quotation : "見積"
    Engineer ||--o{ Quotation : "担当"
    Quotation ||--o{ Order : "発注"
    Order ||--o{ Contract : "契約"
    Engineer ||--o{ Contract : "契約先"
    Project ||--o{ Contract : "案件"
    Contract ||--o{ Invoice : "請求"
    Invoice ||--o{ Payment : "入金"
    Project ||--o{ MatchingResult : "マッチング"
    Engineer ||--o{ MatchingResult : "マッチング"
    User ||--o{ ProcessingJob : "承認者"
    ProcessingJob ||--o{ ProcessingLog : "ログ"
```

---

## 4. ステータス遷移

```mermaid
stateDiagram-v2
    state "案件 (Project)" as proj {
        [*] --> draft_p: 作成
        draft_p --> open: 公開
        open --> in_progress: 進行開始
        in_progress --> completed: 完了
        completed --> closed: クローズ
        open --> closed: 中止
    }

    state "見積 (Quotation)" as quot {
        [*] --> draft_q: 作成
        draft_q --> submitted: 提出
        submitted --> approved: 承認
        submitted --> rejected: 却下
    }

    state "発注 (Order)" as ord {
        [*] --> pending: 作成
        pending --> confirmed: 確定
        pending --> cancelled: キャンセル
    }

    state "契約 (Contract)" as cont {
        [*] --> draft_c: 作成
        draft_c --> active: 発効
        active --> expired: 期間満了
        active --> terminated: 途中解約
    }

    state "請求 (Invoice)" as inv {
        [*] --> draft_i: 作成
        draft_i --> sent: 送付
        sent --> paid: 入金確認
        sent --> overdue: 支払遅延
        overdue --> paid: 入金確認
    }

    state "処理ジョブ (ProcessingJob)" as job {
        [*] --> received: Slack受信
        received --> parsing: 解析開始
        parsing --> routing: 振り分け
        routing --> pending_approval: 承認待ち
        pending_approval --> executing: 承認→実行
        executing --> completed_j: 完了
        pending_approval --> failed: 却下
        executing --> failed: エラー
    }
```

---

## 5. 画面一覧と運用ワークフロー

### 5.1 画面一覧

| パス | 画面名 | 主な機能 |
|------|--------|----------|
| `/login` | ログイン | メールアドレス+パスワード認証 |
| `/dashboard` | ダッシュボード | KPI統計、月次トレンド、最近の活動、エンジニア稼働率 |
| `/companies` | 企業管理 | 企業CRUD（クライアント/ベンダー/SES） |
| `/engineers` | エンジニア管理 | エンジニアCRUD、スキル・雇用形態・単価管理 |
| `/projects` | 案件管理 | 案件CRUD、スキル要件・予算・再委託制限設定 |
| `/quotations` | 見積管理 | 見積CRUD、案件選択→適格エンジニア動的フィルタ |
| `/orders` | 発注管理 | 発注の確認・キャンセル |
| `/contracts` | 契約管理 | 契約CRUD（準委任/請負/派遣） |
| `/invoices` | 請求管理 | 請求CRUD、PDF取込、送付・入金確認 |
| `/jobs` | 処理ジョブ | 自動処理ジョブの監視・承認・却下 |
| `/reconciliation` | 入金消込 | 入金CSVインポート、自動/手動マッチング |
| `/reports` | レポート | 月次レポート生成、スケジュール管理 |

### 5.2 手動運用ワークフロー（データ登録順序）

利用者が画面からデータを登録していく一連の流れ。

```mermaid
flowchart TD
    Start([運用開始]) --> A

    subgraph Master["1. マスタ登録"]
        A[企業を登録<br/>/companies] --> B[エンジニアを登録<br/>/engineers]
        B --> B1[スキル・雇用形態・単価を設定]
    end

    subgraph ProjectPhase["2. 案件登録"]
        C[案件を作成<br/>/projects] --> C1[必須スキル・予算・<br/>再委託制限を設定]
    end

    subgraph MatchPhase["3. マッチング・見積"]
        D[マッチング実行<br/>案件×エンジニア自動スコアリング]
        D --> E[見積を作成<br/>/quotations]
        E --> E1[案件選択→適格エンジニアのみ表示]
        E1 --> E2[単価・工数を入力]
        E2 --> E3[見積を提出→承認]
    end

    subgraph OrderPhase["4. 発注"]
        F[発注を作成<br/>/orders] --> F1[発注を確定]
    end

    subgraph ContractPhase["5. 契約"]
        G[契約を作成<br/>/contracts] --> G1[契約形態・期間・<br/>月単価・精算幅を設定]
        G1 --> G2[契約を発効]
    end

    subgraph BillingPhase["6. 請求・入金"]
        H[請求書を作成<br/>/invoices] --> H1[稼働時間・金額を入力]
        H1 --> H2[請求書を送付]
        H2 --> I[入金CSVをインポート<br/>/reconciliation]
        I --> I1[自動マッチング実行]
        I1 --> I2[消込を確認]
    end

    Master --> ProjectPhase
    ProjectPhase --> MatchPhase
    MatchPhase --> OrderPhase
    OrderPhase --> ContractPhase
    ContractPhase --> BillingPhase

    BillingPhase --> Report[月次レポート生成<br/>/reports]

    style Master fill:#e8f4fd,stroke:#2196f3
    style ProjectPhase fill:#e8f5e9,stroke:#4caf50
    style MatchPhase fill:#fff3e0,stroke:#ff9800
    style OrderPhase fill:#fce4ec,stroke:#e91e63
    style ContractPhase fill:#f3e5f5,stroke:#9c27b0
    style BillingPhase fill:#e0f2f1,stroke:#009688
```

### 5.3 Slack自動化ワークフロー

Excel発注仕様書をSlackに投稿するだけで、案件・見積・発注が自動登録される。

```mermaid
flowchart TD
    S1[担当者がSlackに<br/>Excel発注仕様書を投稿] --> S2[Slack Webhook受信<br/>POST /api/v1/slack/events]
    S2 --> S3[Excelファイルをダウンロード]
    S3 --> S4{フォーマット判定}

    S4 -->|一覧形式| S5A[テーブルパース<br/>行ごとにジョブ作成]
    S4 -->|仕様書形式| S5B[Key-Valueパース<br/>1ジョブ作成]

    S5A --> S6[振り分けエンジン<br/>ルールマッチング]
    S5B --> S6

    S6 --> S7[Slackに承認依頼を送信<br/>承認/却下ボタン付き]
    S7 --> S8{担当者の判断}

    S8 -->|承認| S9[自動データ登録]
    S8 -->|却下| S10[ジョブをfailedに更新<br/>Slack通知]

    subgraph AutoRegister["自動登録処理"]
        S9 --> R1[企業を検索/作成]
        R1 --> R2[案件を作成<br/>再委託制限も反映]
        R2 --> R3[適格エンジニアを<br/>自動アサイン]
        R3 --> R4[見積を作成<br/>status: approved]
        R4 --> R5[発注を作成<br/>ORD-YYYYMMDD-NNN]
    end

    S9 --> S11[MCPサーバー経由で<br/>Webシステムに自動入力]
    S11 --> S12[Slack完了通知<br/>受注番号・スクリーンショット]

    style AutoRegister fill:#e8f5e9,stroke:#4caf50
```

### 5.4 見積作成時の商流チェックフロー

```mermaid
flowchart TD
    Q1[見積作成画面を開く] --> Q2[案件を選択]
    Q2 --> Q3[GET /engineers/eligible?project_id=X<br/>適格エンジニアAPIを呼び出し]
    Q3 --> Q4{案件に再委託制限あり？}

    Q4 -->|なし| Q5A[全エンジニアを表示]
    Q4 -->|あり| Q5B[制限を満たすエンジニアのみ表示<br/>警告バナーで制限内容を明示]

    Q5A --> Q6[エンジニアを選択]
    Q5B --> Q6

    Q6 --> Q7[単価・工数を入力]
    Q7 --> Q8[保存ボタン]
    Q8 --> Q9[POST /quotations<br/>サーバー側でも商流バリデーション]
    Q9 --> Q10{バリデーション}

    Q10 -->|OK| Q11[見積作成成功]
    Q10 -->|NG| Q12[400エラー<br/>商流制約違反メッセージ]

    style Q5B fill:#fff3e0,stroke:#ff9800
    style Q12 fill:#fce4ec,stroke:#e91e63
```

---

## 6. SES商流制約（再委託制限）

### 6.1 エンジニアのtier算出ルール

| 雇用形態 | 所属企業 | Tier | 説明 |
|----------|----------|------|------|
| `proper` | - | 0 | 自社正社員（プロパー） |
| `first_tier_proper` | - | 1 | 一社先のプロパー社員 |
| `freelancer` | なし | 1 | 直接契約の個人事業主 |
| `first_tier_freelancer` | - | 2 | 一社先の個人事業主 |
| `freelancer` | あり | 2 | パートナー企業経由の個人事業主 |

### 6.2 案件の再委託制限と許可tier

| 制限 | 許可tier | 説明 |
|------|----------|------|
| `proper_only` | 0のみ | プロパーのみ |
| `first_tier` | 0, 1 | 一社先まで |
| `second_tier` | 0, 1, 2 | 二社先まで |
| `no_restriction` / null | 全て | 制限なし |

### 6.3 適格判定マトリクス

| | proper<br/>(tier 0) | first_tier_proper<br/>(tier 1) | freelancer直接<br/>(tier 1) | first_tier_freelancer<br/>(tier 2) | freelancer+企業<br/>(tier 2) |
|---|:---:|:---:|:---:|:---:|:---:|
| **proper_only** | OK | NG | NG | NG | NG |
| **first_tier** | OK | OK | OK | NG | NG |
| **second_tier** | OK | OK | OK | OK | OK |
| **no_restriction** | OK | OK | OK | OK | OK |

---

## 7. 入金消込（Payment Reconciliation）

### 7.1 処理フロー

```mermaid
flowchart TD
    P1[銀行から入金CSVをダウンロード] --> P2[入金消込画面で<br/>CSVインポート]
    P2 --> P3[Paymentレコード作成<br/>status: unmatched]
    P3 --> P4[自動マッチング実行]

    P4 --> P5{各入金に対して<br/>未払い請求書とスコア計算}

    P5 --> P6[金額一致: +50pt<br/>金額近似1%以内: +30pt<br/>支払者名一致: +30pt<br/>振込番号に請求番号含む: +20pt]

    P6 --> P7{スコア >= 50?}
    P7 -->|Yes| P8[自動マッチング<br/>status: matched]
    P7 -->|No| P9[未マッチのまま]

    P8 --> P10[担当者が確認]
    P9 --> P11[担当者が手動マッチング<br/>請求書を選択]

    P10 --> P12[消込確定<br/>Payment: confirmed<br/>Invoice: paid]
    P11 --> P10

    style P6 fill:#fff3e0,stroke:#ff9800
```

### 7.2 ファジーマッチング

- 企業名の正規化: `株式会社`/`(株)`/`有限会社`等の接頭辞を除去
- カタカナ正規化（全角→NFKC）
- Levenshtein距離による類似度判定（閾値: 0.7）

---

## 8. マッチングアルゴリズム（案件×エンジニア）

```
スコア = (スキル一致率 × 0.5) + (単価適合 × 0.25) + (稼働可否 × 0.25)

※ 商流不適格の場合はスコア = 0
```

| 要素 | 配点 | 判定条件 |
|------|------|----------|
| スキル一致率 | 0.0 - 0.5 | 一致スキル数 / 必須スキル数 × 0.5 |
| 単価適合 | 0 or 0.25 | エンジニア月単価 ≤ 案件予算 |
| 稼働可否 | 0 or 0.25 | availability_status == available |
| 商流適格 | - | 不適格の場合スコアを0に上書き |

---

## 9. APIエンドポイント一覧

### 認証

| Method | Path | 説明 |
|--------|------|------|
| POST | `/api/v1/auth/login` | ログイン（JWT発行） |
| POST | `/api/v1/auth/signup` | ユーザー登録 |
| GET | `/api/v1/auth/me` | 自分の情報取得 |

### マスタ管理

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/companies` | 企業一覧（ページネーション、type/searchフィルタ） |
| POST | `/api/v1/companies` | 企業作成 |
| GET | `/api/v1/companies/{id}` | 企業詳細 |
| PUT | `/api/v1/companies/{id}` | 企業更新 |
| DELETE | `/api/v1/companies/{id}` | 企業削除（admin） |
| GET | `/api/v1/engineers` | エンジニア一覧（availability/company/searchフィルタ） |
| GET | `/api/v1/engineers/eligible` | 案件適格エンジニア一覧 |
| POST | `/api/v1/engineers` | エンジニア作成（スキル紐付け） |
| GET | `/api/v1/engineers/{id}` | エンジニア詳細 |
| PUT | `/api/v1/engineers/{id}` | エンジニア更新 |
| DELETE | `/api/v1/engineers/{id}` | エンジニア削除（admin） |

### 案件・見積・発注

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/projects` | 案件一覧（status/client_companyフィルタ） |
| POST | `/api/v1/projects` | 案件作成（スキル要件紐付け） |
| GET | `/api/v1/projects/{id}` | 案件詳細 |
| PUT | `/api/v1/projects/{id}` | 案件更新 |
| DELETE | `/api/v1/projects/{id}` | 案件削除（admin） |
| GET | `/api/v1/quotations` | 見積一覧（status/projectフィルタ） |
| POST | `/api/v1/quotations` | 見積作成（商流バリデーション） |
| GET | `/api/v1/quotations/{id}` | 見積詳細 |
| PUT | `/api/v1/quotations/{id}` | 見積更新 |
| DELETE | `/api/v1/quotations/{id}` | 見積削除（admin） |
| POST | `/api/v1/quotations/{id}/submit` | 見積提出 |
| POST | `/api/v1/quotations/{id}/approve` | 見積承認 |
| GET | `/api/v1/orders` | 発注一覧 |
| POST | `/api/v1/orders` | 発注作成 |
| GET | `/api/v1/orders/{id}` | 発注詳細 |
| PUT | `/api/v1/orders/{id}` | 発注更新 |
| DELETE | `/api/v1/orders/{id}` | 発注削除（admin） |
| POST | `/api/v1/orders/{id}/confirm` | 発注確定 |

### 契約・請求

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/contracts` | 契約一覧（status/engineer/projectフィルタ） |
| POST | `/api/v1/contracts` | 契約作成 |
| GET | `/api/v1/contracts/{id}` | 契約詳細 |
| PUT | `/api/v1/contracts/{id}` | 契約更新 |
| DELETE | `/api/v1/contracts/{id}` | 契約削除（admin） |
| GET | `/api/v1/invoices` | 請求一覧（status/contractフィルタ） |
| POST | `/api/v1/invoices` | 請求作成 |
| GET | `/api/v1/invoices/{id}` | 請求詳細 |
| PUT | `/api/v1/invoices/{id}` | 請求更新 |
| DELETE | `/api/v1/invoices/{id}` | 請求削除（admin） |
| POST | `/api/v1/invoices/{id}/send` | 請求送付 |
| POST | `/api/v1/invoices/{id}/pay` | 入金確認 |
| POST | `/api/v1/invoices/import` | 請求書PDFインポート |

### マッチング

| Method | Path | 説明 |
|--------|------|------|
| POST | `/api/v1/matching/run` | マッチング実行 |
| GET | `/api/v1/matching/results` | マッチング結果一覧 |

### 自動化

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/jobs` | 処理ジョブ一覧 |
| GET | `/api/v1/jobs/{id}` | ジョブ詳細 |
| POST | `/api/v1/jobs/{id}/approve` | ジョブ承認/却下 |
| GET | `/api/v1/jobs/tasks/{task_id}/status` | 非同期タスク状況 |
| POST | `/api/v1/slack/events` | Slack Event Webhook |
| POST | `/api/v1/slack/interactions` | Slack Interactive Webhook |

### ダッシュボード

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/v1/dashboard/stats` | KPI統計 |
| GET | `/api/v1/dashboard/recent-activities` | 最近の活動 |
| GET | `/api/v1/dashboard/monthly-trends` | 月次トレンド（6ヶ月） |
| GET | `/api/v1/dashboard/engineer-utilization` | エンジニア稼働率 |

### 入金消込

| Method | Path | 説明 |
|--------|------|------|
| POST | `/api/v1/reconciliation/import` | 入金CSVインポート |
| POST | `/api/v1/reconciliation/match` | 自動マッチング実行 |
| GET | `/api/v1/reconciliation` | 入金一覧 |
| GET | `/api/v1/reconciliation/summary` | 消込サマリー |
| POST | `/api/v1/reconciliation/{id}/match` | 手動マッチング |
| POST | `/api/v1/reconciliation/{id}/confirm` | 消込確定 |
| POST | `/api/v1/reconciliation/{id}/unmatch` | マッチング取消 |

### レポート

| Method | Path | 説明 |
|--------|------|------|
| POST | `/api/v1/reports/generate` | レポート生成（Excel） |
| GET | `/api/v1/reports/types` | レポート種別一覧 |
| GET | `/api/v1/reports/schedules` | スケジュール一覧 |
| POST | `/api/v1/reports/schedules` | スケジュール作成 |
| PUT | `/api/v1/reports/schedules/{id}` | スケジュール更新 |
| DELETE | `/api/v1/reports/schedules/{id}` | スケジュール削除（admin） |

### ヘルスチェック

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/health` | サーバー稼働確認 |

---

## 10. 認証・認可

### 認証フロー

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant FE as フロントエンド
    participant API as FastAPI
    participant DB as PostgreSQL

    User->>FE: メール+パスワード入力
    FE->>API: POST /api/v1/auth/login
    API->>DB: ユーザー検索 + bcrypt照合
    DB-->>API: ユーザー情報
    API-->>FE: JWT access_token
    FE->>FE: localStorageに保存

    Note over FE,API: 以降のリクエスト

    FE->>API: Authorization: Bearer {token}
    API->>API: JWT検証 (HS256)
    API->>DB: ユーザー取得
    API-->>FE: レスポンス

    Note over FE,API: トークン期限切れ時

    FE->>API: 期限切れトークン
    API-->>FE: 401 Unauthorized
    FE->>FE: ログアウト→/loginにリダイレクト
```

### ロール権限

| 操作 | admin | sales | engineer |
|------|:-----:|:-----:|:--------:|
| データ閲覧 | OK | OK | OK |
| データ作成・更新 | OK | OK | - |
| データ削除 | OK | - | - |
| ジョブ承認 | OK | OK | - |
| レポート生成 | OK | OK | - |

---

## 11. Docker構成

```mermaid
graph LR
    subgraph DockerCompose["Docker Compose"]
        FE[frontend<br/>Vite :5173]
        BE[backend<br/>FastAPI :8000]
        WK[worker<br/>Celery]
        BT[beat<br/>Celery Beat]
        DB[(db<br/>PostgreSQL :5432)]
        RD[(redis<br/>Redis :6379)]
    end

    FE -->|proxy /api| BE
    BE --> DB
    BE --> RD
    WK --> DB
    WK --> RD
    BT --> RD

    style DB fill:#336791,color:#fff
    style RD fill:#d82c20,color:#fff
```

| サービス | イメージ | ポート | 役割 |
|----------|---------|--------|------|
| db | postgres:16 | 5432 | データベース |
| redis | redis:7 | 6379 | ジョブキュー |
| backend | python:3.12 | 8000 | APIサーバー |
| frontend | node:20 | 5173 | フロントエンド開発サーバー |
| worker | python:3.12 | - | 非同期ジョブ実行 |
| beat | python:3.12 | - | 定期ジョブスケジューラ |

---

## 12. Alembicマイグレーション履歴

| Revision | 説明 |
|----------|------|
| `644191d9d074` | 初期スキーマ（全テーブル作成） |
| `abeb11174ac4` | payments テーブル追加 |
| `c3f8a2d1e5b7` | 商流制約フィールド追加（employment_type, subcontracting_tier_limit, tier_eligible） |
| `d4e5f6a7b8c9` | 新商流enum値追加（first_tier_proper, first_tier_freelancer, second_tier） |

---

## 13. テスト

- **テストフレームワーク**: pytest
- **テストDB**: SQLite in-memory
- **テスト数**: 210件（うち1件は既知の未実装モジュール依存で失敗）
- **実行コマンド**: `PYTHONPATH=. .venv/bin/python -m pytest tests/ -x -v`

| テストファイル | テスト数 | 対象 |
|----------------|----------|------|
| test_auth.py | 6 | 認証（signup/login/me） |
| test_companies.py | 8 | 企業CRUD |
| test_engineers.py | 14 | エンジニアCRUD + 適格API |
| test_projects.py | 8 | 案件CRUD |
| test_quotations.py | 15 | 見積CRUD + 商流バリデーション |
| test_orders.py | 8 | 発注CRUD |
| test_contracts.py | 7 | 契約CRUD |
| test_invoices.py | 10 | 請求CRUD |
| test_matching.py | 8 | マッチングアルゴリズム |
| test_tier_eligibility.py | 30 | 商流制約ロジック全組み合わせ |
| test_dashboard.py | 9 | ダッシュボードAPI |
| test_jobs.py | 14 | 処理ジョブ + 自動登録 |
| test_slack.py | 17 | Slack連携 |
| test_reconciliation.py | 30 | 入金消込 + ファジーマッチ |
| test_rbac.py | 15 | ロールベースアクセス制御 |
| test_reports.py | 11 | レポート生成 |
