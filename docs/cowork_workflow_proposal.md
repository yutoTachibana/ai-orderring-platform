# Claude Cowork導入による受発注ワークフロー改善提案

## 1. 現状のワークフロー（As-Is）

### 概要

現在の受発注業務は、Slack・Excel・2つのWeb受発注システムにまたがる**手動入力中心のフロー**で運用されている。

1. Slack経由で発注仕様書（Excel）を受領
2. Excel の内容を確認し、2つのWeb受発注システムに手動で振り分け・入力
3. 入力結果やステータスをExcelに転記し、一元管理

### As-Is フロー図

```mermaid
flowchart TD
    A["📩 Slackで発注仕様書\n（Excel）を受領"] --> B["👁️ 担当者がExcelを\n目視確認・内容精査"]
    B --> C{"発注先の\n振り分け判断"}
    C -->|"パターンA"| D["🖥️ Web受発注システムA\nに手動入力"]
    C -->|"パターンB"| E["🖥️ Web受発注システムB\nに手動入力"]
    D --> F["📝 Excelに入力内容・\nステータスを転記"]
    E --> F
    F --> G["📊 管理用Excelで\n一元管理・進捗追跡"]
    G --> H{"ステータス更新\n発生？"}
    H -->|"あり"| I["手動でExcelを更新"]
    I --> G
    H -->|"なし"| J["完了"]

    style A fill:#ffcccc
    style D fill:#ffffcc
    style E fill:#ffffcc
    style F fill:#ffffcc
    style I fill:#ffffcc
```

### 現状の課題

| 課題 | 詳細 |
|------|------|
| **二重入力** | Excel → Webシステムへの転記が2系統で発生 |
| **転記ミスのリスク** | 手動コピーによる入力漏れ・誤入力 |
| **ステータス反映の遅延** | Webシステムの状態変化を手動でExcelに反映 |
| **属人化** | 振り分けルールやシステム操作が担当者依存 |
| **作業時間の浪費** | 単純転記に知識労働者の時間を消費 |

---

## 2. Cowork導入後のワークフロー（To-Be）

### Claude Coworkとは

Claude Coworkは、Claude Desktopアプリ上で動作するエージェント機能である。主な特長は以下のとおり。

- **ローカルファイルへの直接アクセス** — Excel等のファイルをアップロード不要で読み書き可能
- **サブエージェント並列処理** — 複雑なタスクを分割し、複数ワークストリームを同時実行
- **プロフェッショナルな出力** — 数式・書式付きExcelやレポートを直接生成
- **長時間タスクの継続実行** — タイムアウトなしにマルチステップ処理を完遂
- **MCP（Model Context Protocol）連携** — 外部ツールやカスタムサーバーと接続し、Coworkの機能を拡張可能

### カスタムMCPサーバーによるWebシステム自動入力

本提案では、各Web受発注システムに対応した**カスタムMCPサーバー**を構築し、CoworkからWebシステムへの入力を完全自動化する。

```mermaid
flowchart LR
    subgraph "Claude Cowork"
        CW["🤖 Coworkエージェント"]
    end

    subgraph "カスタムMCPサーバー"
        MCP_A["MCP Server A\n（Selenium実行環境）"]
        MCP_B["MCP Server B\n（Selenium実行環境）"]
    end

    subgraph "Web受発注システム"
        WA["🌐 WebシステムA"]
        WB["🌐 WebシステムB"]
    end

    CW -->|"MCP呼び出し\n入力データ送信"| MCP_A
    CW -->|"MCP呼び出し\n入力データ送信"| MCP_B
    MCP_A -->|"Seleniumで\nブラウザ操作"| WA
    MCP_B -->|"Seleniumで\nブラウザ操作"| WB
    WA -->|"実行結果\n返却"| MCP_A
    WB -->|"実行結果\n返却"| MCP_B
    MCP_A -->|"成功/失敗\nレスポンス"| CW
    MCP_B -->|"成功/失敗\nレスポンス"| CW

    style CW fill:#ccffcc
    style MCP_A fill:#cce5ff
    style MCP_B fill:#cce5ff
```

#### MCPサーバーの構成

各MCPサーバーは、対応するWebシステム専用のSeleniumコードをラップした実行環境として機能する。

| コンポーネント | 役割 |
|--------------|------|
| **MCP Server A** | WebシステムA専用のSeleniumスクリプトを実行。ログイン→フォーム入力→送信→結果取得を自動化 |
| **MCP Server B** | WebシステムB専用のSeleniumスクリプトを実行。同上 |
| **共通インターフェース** | Coworkからの入力データ（JSON）を受け取り、Seleniumへ橋渡し。実行結果を構造化して返却 |

### To-Be フロー図

```mermaid
flowchart TD
    A["📩 Slackで発注仕様書\n（Excel）を受領"] --> B["🤖 Coworkタスク起動\n「発注仕様書を処理して」"]
    B --> C["📖 Coworkが自動で\nExcelを読み取り・解析"]
    C --> D{"Coworkが発注先を\n自動振り分け"}
    D -->|"パターンA"| E["📋 サブエージェントA\n入力データ生成・\n入力内容サマリ表示"]
    D -->|"パターンB"| F["📋 サブエージェントB\n入力データ生成・\n入力内容サマリ表示"]
    E --> G["👤 担当者が入力内容を\n確認・承認"]
    F --> G
    G -->|"承認"| H["🤖 CoworkがMCPサーバー\n経由でSelenium実行"]
    G -->|"修正指示"| I["🤖 Coworkが\nデータ修正"]
    I --> G
    H --> J["🌐 MCPサーバーが\nWebシステムに自動入力"]
    J --> K["🤖 Coworkが実行結果を\n確認・管理Excelを自動更新"]
    K --> L["📊 管理用Excelに\nステータス・入力内容\nが自動反映"]
    L --> M["✅ 完了"]

    style B fill:#ccffcc
    style C fill:#ccffcc
    style D fill:#ccffcc
    style E fill:#ccffcc
    style F fill:#ccffcc
    style H fill:#ccffcc
    style J fill:#cce5ff
    style K fill:#ccffcc
```

> **ポイント:** 担当者の役割は**入力内容の確認・承認のみ**。承認後はCoworkがMCPサーバー（Selenium実行環境）を呼び出し、Webシステムへの入力から管理Excelの更新まで全自動で処理する。

### 処理の詳細フロー

```mermaid
sequenceDiagram
    participant S as Slack
    participant U as 担当者
    participant CW as Claude Cowork
    participant FS as ローカルファイル
    participant MCP_A as MCP Server A<br/>（Selenium）
    participant MCP_B as MCP Server B<br/>（Selenium）
    participant WA as WebシステムA
    participant WB as WebシステムB

    S->>U: 発注仕様書（Excel）受領通知
    U->>FS: 仕様書Excelをローカルに保存
    U->>CW: タスク指示「発注仕様書を処理」

    activate CW
    CW->>FS: Excelファイル読み取り
    CW->>CW: 内容解析・振り分けルール適用
    CW->>CW: サブエージェント起動（並列処理）
    CW->>CW: 入力データ生成・バリデーション
    CW->>U: 入力内容サマリを提示<br/>「以下の内容でWebシステムに<br/>入力してよいですか？」
    deactivate CW

    U->>CW: 確認OK（承認）

    activate CW
    par システムA向け自動入力
        CW->>MCP_A: 入力データ送信（JSON）
        activate MCP_A
        MCP_A->>WA: Seleniumでログイン・フォーム入力・送信
        WA-->>MCP_A: 入力完了・確認番号返却
        MCP_A-->>CW: 実行結果（成功/失敗・確認番号）
        deactivate MCP_A
    and システムB向け自動入力
        CW->>MCP_B: 入力データ送信（JSON）
        activate MCP_B
        MCP_B->>WB: Seleniumでログイン・フォーム入力・送信
        WB-->>MCP_B: 入力完了・確認番号返却
        MCP_B-->>CW: 実行結果（成功/失敗・確認番号）
        deactivate MCP_B
    end

    CW->>FS: 管理Excelにレコード追加<br/>（確認番号・ステータス含む）
    CW->>U: 処理完了報告<br/>「全件の入力が完了しました」
    deactivate CW
```

### MCPサーバーの処理フロー（内部詳細）

```mermaid
flowchart TD
    A["Coworkから\n入力データ（JSON）受信"] --> B["入力データの\nスキーマバリデーション"]
    B -->|"OK"| C["Seleniumドライバー起動\n（Headlessモード）"]
    B -->|"NG"| Z["エラーレスポンス返却"]
    C --> D["対象Webシステムにログイン"]
    D -->|"成功"| E["発注フォームに遷移"]
    D -->|"失敗"| Y["リトライ\n（最大3回）"]
    Y -->|"成功"| E
    Y -->|"失敗"| Z
    E --> F["フォームに\nデータ入力"]
    F --> G["入力内容の\nスクリーンショット取得"]
    G --> H["送信ボタン\nクリック"]
    H --> I["確認画面の\n内容を検証"]
    I -->|"一致"| J["確認番号・\n完了ステータス取得"]
    I -->|"不一致"| Z
    J --> K["Seleniumドライバー終了"]
    K --> L["実行結果を\nCoworkに返却"]

    style A fill:#cce5ff
    style G fill:#fff3cc
    style L fill:#ccffcc
    style Z fill:#ffcccc
```

---

## 3. Cowork + MCP導入による改善効果

### 担当者の役割変化

```mermaid
pie title 担当者の作業内訳（導入後）
    "入力内容の確認・承認" : 60
    "例外対応・エラー確認" : 25
    "ルール更新・改善指示" : 15
```

> 従来の「手作業」は完全に排除され、担当者は**確認・判断業務に集中**できる。

### 効果まとめ

| 観点 | 現状（As-Is） | Cowork + MCP導入後（To-Be） |
|------|--------------|---------------------------|
| **Excel読み取り** | 手動で目視確認 | Coworkが自動解析 |
| **振り分け判断** | 担当者が都度判断 | ルールベースで自動分類 |
| **入力データ準備** | 手動で転記 | Coworkがシステム別にデータ整形 |
| **Web入力** | 担当者が手動入力 | **MCPサーバー（Selenium）が自動入力** |
| **入力内容の確認** | 入力後に目視チェック | **入力前にCoworkがサマリ提示→担当者が承認** |
| **管理Excel更新** | 手動転記 | Coworkが自動更新（確認番号含む） |
| **担当者の役割** | データ入力作業者 | **確認・承認・判断のみ** |
| **処理時間** | 1件あたり15〜30分 | **1件あたり2〜5分（承認時間のみ）** |
| **ミス発生率** | 転記ミスが散発 | バリデーション+スクリーンショット検証で大幅削減 |
| **夜間・休日対応** | 不可（人手が必要） | **事前承認済みなら自動実行可能** |

---

## 4. システム構成

```mermaid
graph TB
    subgraph "担当者の端末"
        CD["Claude Desktop\n（Cowork）"]
        FS["ローカルファイル\n（Excel等）"]
    end

    subgraph "MCPサーバー群（ローカル or サーバー）"
        MCP_A["MCP Server A\nSelenium + WebDriverA用スクリプト\n（Python）"]
        MCP_B["MCP Server B\nSelenium + WebDriverB用スクリプト\n（Python）"]
    end

    subgraph "外部Webシステム"
        WA["Web受発注システムA"]
        WB["Web受発注システムB"]
    end

    CD <-->|"ファイル読み書き"| FS
    CD <-->|"MCP Protocol\n（stdio/SSE）"| MCP_A
    CD <-->|"MCP Protocol\n（stdio/SSE）"| MCP_B
    MCP_A <-->|"HTTP/HTTPS\n（Selenium）"| WA
    MCP_B <-->|"HTTP/HTTPS\n（Selenium）"| WB

    style CD fill:#ccffcc
    style MCP_A fill:#cce5ff
    style MCP_B fill:#cce5ff
```

---

## 5. 導入ステップ

```mermaid
gantt
    title Cowork + MCP 導入ロードマップ
    dateFormat YYYY-MM-DD
    section Phase 1：準備
        振り分けルールの整理・文書化           :a1, 2025-01-01, 14d
        管理Excelのフォーマット標準化           :a2, after a1, 7d
        WebシステムA/Bの画面フロー調査          :a3, 2025-01-01, 14d
    section Phase 2：MCP開発
        MCPサーバーA（Selenium）開発             :b1, after a2, 21d
        MCPサーバーB（Selenium）開発             :b2, after a2, 21d
        エラーハンドリング・リトライ実装          :b3, after b1, 7d
        スクリーンショット検証機能実装            :b4, after b1, 7d
    section Phase 3：パイロット
        Coworkタスクテンプレート作成              :c1, after b3, 7d
        少量データでのE2E検証                   :c2, after c1, 14d
        精度検証・ルール調整                    :c3, after c2, 7d
    section Phase 4：本番運用
        全件Cowork + MCP経由に切り替え           :d1, after c3, 14d
        運用手順書整備                          :d2, after c3, 7d
        継続的改善・Webシステム変更追従            :d3, after d1, 30d
```

---

## 6. 留意事項

- **MCPサーバーのメンテナンス**: WebシステムのUI変更時にSeleniumスクリプトの更新が必要。画面要素の特定にはIDやdata属性を優先し、変更に強い設計とすること。
- **認証情報の管理**: Webシステムへのログイン認証情報はMCPサーバー側で安全に管理する（環境変数や秘密管理ツールを使用）。Cowork側には認証情報を渡さない設計とする。
- **エラー時のフォールバック**: Selenium実行が失敗した場合、Coworkが担当者にエラー内容を通知し、手動対応を促すフローを用意する。
- **スクリーンショットによる証跡**: MCPサーバーは入力完了時のスクリーンショットを保存し、監査証跡として管理Excelにパスを記録する。
- **セキュリティ**: Coworkはローカルファイルにアクセスするため、アクセス権限を適切に設定すること。MCPサーバーへの接続は信頼できる環境（localhost等）に限定する。
- **セッション管理**: Cowork実行中はClaude Desktopアプリを閉じないこと。アプリを閉じるとセッションが終了する。
- **利用プラン**: CoworkはMaxプラン限定（macOS Claude Desktopアプリのみ）のリサーチプレビューである。
