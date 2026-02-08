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

### To-Be フロー図

```mermaid
flowchart TD
    A["📩 Slackで発注仕様書\n（Excel）を受領"] --> B["🤖 Coworkタスク起動\n「発注仕様書を処理して」"]
    B --> C["📖 Coworkが自動で\nExcelを読み取り・解析"]
    C --> D{"Coworkが発注先を\n自動振り分け"}
    D -->|"パターンA"| E["🌐 サブエージェントA\nWebシステムAへ入力指示\n生成"]
    D -->|"パターンB"| F["🌐 サブエージェントB\nWebシステムBへ入力指示\n生成"]
    E --> G["👤 担当者がシステムAへ\n入力（入力値はCowork\nが準備済み）"]
    F --> H["👤 担当者がシステムBへ\n入力（入力値はCowork\nが準備済み）"]
    G --> I["🤖 Coworkが管理Excel\nを自動更新"]
    H --> I
    I --> J["📊 管理用Excelに\nステータス・入力内容\nが自動反映"]
    J --> K["✅ 完了"]

    style B fill:#ccffcc
    style C fill:#ccffcc
    style D fill:#ccffcc
    style E fill:#ccffcc
    style F fill:#ccffcc
    style I fill:#ccffcc
```

> **注記:** 現時点ではCoworkはWebシステムへの直接ログイン・操作を自動で行うことはセキュリティ上推奨されない。Webシステムへの入力自体は担当者が行うが、入力データの準備・整形・振り分けと管理Excelの更新をCoworkが担う。

### 処理の詳細フロー

```mermaid
sequenceDiagram
    participant S as Slack
    participant U as 担当者
    participant CW as Claude Cowork
    participant FS as ローカルファイル
    participant WA as WebシステムA
    participant WB as WebシステムB

    S->>U: 発注仕様書（Excel）受領通知
    U->>FS: 仕様書Excelをローカルに保存
    U->>CW: タスク指示「発注仕様書を処理」

    activate CW
    CW->>FS: Excelファイル読み取り
    CW->>CW: 内容解析・振り分けルール適用
    CW->>CW: サブエージェント起動（並列処理）

    par システムA向け処理
        CW->>FS: システムA用入力データシート生成
    and システムB向け処理
        CW->>FS: システムB用入力データシート生成
    end

    CW->>FS: 管理Excelにレコード追加
    CW->>U: 処理完了通知 + 入力指示サマリ
    deactivate CW

    U->>FS: 入力データシート確認
    U->>WA: システムA用データを入力
    U->>WB: システムB用データを入力
    U->>CW: 入力完了を報告

    activate CW
    CW->>FS: 管理Excelのステータスを更新
    deactivate CW
```

---

## 3. Cowork導入による改善効果

### 自動化される作業

```mermaid
pie title 作業時間の配分変化（イメージ）
    "Excel読み取り・解析（自動化）" : 25
    "振り分け判断（自動化）" : 15
    "入力データ整形（自動化）" : 20
    "管理Excel更新（自動化）" : 20
    "Webシステム入力（担当者）" : 15
    "確認・承認（担当者）" : 5
```

### 効果まとめ

| 観点 | 現状（As-Is） | Cowork導入後（To-Be） |
|------|--------------|----------------------|
| **Excel読み取り** | 手動で目視確認 | Coworkが自動解析 |
| **振り分け判断** | 担当者が都度判断 | ルールベースで自動分類 |
| **入力データ準備** | 手動で転記 | Coworkがシステム別にデータ整形 |
| **Web入力** | 手動（変更なし） | 担当者が実施（ただしデータは準備済み） |
| **管理Excel更新** | 手動転記 | Coworkが自動更新 |
| **処理時間** | 1件あたり15〜30分 | 1件あたり5〜10分（推定） |
| **ミス発生率** | 転記ミスが散発 | データ準備段階でのミス大幅削減 |

---

## 4. 導入ステップ

```mermaid
gantt
    title Cowork導入ロードマップ
    dateFormat YYYY-MM-DD
    section Phase 1：準備
        振り分けルールの整理・文書化       :a1, 2025-01-01, 14d
        管理Excelのフォーマット標準化       :a2, after a1, 7d
    section Phase 2：パイロット
        Coworkタスクテンプレート作成         :b1, after a2, 14d
        少量データでの検証                  :b2, after b1, 14d
        精度検証・ルール調整                :b3, after b2, 7d
    section Phase 3：本番運用
        全件Cowork経由に切り替え             :c1, after b3, 14d
        運用手順書整備                      :c2, after b3, 7d
        継続的改善                          :c3, after c1, 30d
```

---

## 5. 留意事項

- **Webシステムへの直接操作**: Coworkは現時点ではWebブラウザ操作の完全自動化を保証しない。Webシステムへの入力は引き続き担当者が行う想定とする。将来的にClaude in Chrome等との連携で自動化範囲を拡大できる可能性がある。
- **セキュリティ**: Coworkはローカルファイルにアクセスするため、アクセス権限を適切に設定すること。機密性の高い発注情報を扱う場合は、Claudeの計画を確認してから実行を許可する。
- **セッション管理**: Cowork実行中はClaude Desktopアプリを閉じないこと。アプリを閉じるとセッションが終了する。
- **利用プラン**: CoworkはMaxプラン限定（macOS Claude Desktopアプリのみ）のリサーチプレビューである。
