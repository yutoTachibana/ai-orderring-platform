# Claude Cowork を中心としたビジネスプロセス全体最適化提案

## エグゼクティブサマリー

前回の提案では「現行業務の部分的な自動化」に留まっていた。本提案では、Claude Coworkの**エージェント機能・MCP連携・スキル機能・並列処理**をフル活用し、受発注業務を含むビジネスプロセス全体を再設計する。

ポイントは3つ：

1. **Slack → Cowork を直結**し、人が介在しない仕組みを作る
2. **Claude in Chrome との連携**で Web 受発注システムへの入力も自動化する
3. **スキル（再利用可能ワークフロー）** により、属人化を排除し組織ナレッジ化する

---

## 1. 前回提案との比較

```mermaid
flowchart LR
    subgraph 前回提案
        direction TB
        A1["Excelの読み取り・\n振り分けを自動化"] --> A2["Webシステム入力は\n手動のまま"]
        A2 --> A3["管理Excel更新を\n自動化"]
    end

    subgraph 本提案
        direction TB
        B1["Slack受領を\n自動トリガー化"] --> B2["Excel解析〜\nWebシステム入力まで\nEnd-to-End自動化"]
        B2 --> B3["ステータス監視〜\nレポーティングまで\n自動化"]
    end

    前回提案 -->|"さらに進化"| 本提案

    style A2 fill:#ffffcc
    style B1 fill:#ccffcc
    style B2 fill:#ccffcc
    style B3 fill:#ccffcc
```

| 比較軸 | 前回提案 | 本提案 |
|--------|---------|--------|
| 自動化範囲 | Excel読み取り〜データ準備 | Slack受領〜Web入力〜レポートまで |
| Web入力 | 手動（データ準備のみ自動） | Claude in Chrome連携で自動化 |
| トリガー | 手動でCowork起動 | Slackコネクタで自動検知 |
| 再利用性 | 毎回プロンプト記述 | スキルとして保存・再利用 |
| 並列処理 | 未活用 | サブエージェントで並列実行 |
| 異常検知 | なし | バリデーション＋Slack通知 |

---

## 2. 理想のアーキテクチャ全体像

```mermaid
graph TB
    subgraph "入力層"
        S["📩 Slack\n（発注仕様書チャネル）"]
        E["📎 添付Excel\n（発注仕様書）"]
    end

    subgraph "Claude Cowork エージェント層"
        CW["🤖 Cowork\nオーケストレーター"]
        SK["📋 スキル\n（受発注処理）"]
        SA1["🔀 サブエージェントA\nシステムA入力担当"]
        SA2["🔀 サブエージェントB\nシステムB入力担当"]
        SA3["📊 サブエージェントC\nExcel更新・レポート担当"]
    end

    subgraph "外部連携層"
        SC["🔌 Slackコネクタ\n（MCP）"]
        CC["🌐 Claude in Chrome\n（ブラウザ操作）"]
        FS["📁 ローカルファイル\nシステム"]
    end

    subgraph "出力層"
        WA["🖥️ Web受発注\nシステムA"]
        WB["🖥️ Web受発注\nシステムB"]
        MG["📊 管理Excel"]
        SN["📩 Slack通知\n（完了/異常）"]
    end

    S --> SC
    E --> FS
    SC --> CW
    FS --> CW
    CW --> SK
    SK --> SA1 & SA2 & SA3
    SA1 --> CC --> WA
    SA2 --> CC --> WB
    SA3 --> FS --> MG
    CW --> SC --> SN

    style CW fill:#4CAF50,color:#fff
    style SK fill:#2196F3,color:#fff
    style SA1 fill:#FF9800,color:#fff
    style SA2 fill:#FF9800,color:#fff
    style SA3 fill:#FF9800,color:#fff
```

---

## 3. 詳細ワークフロー

### 3.1 End-to-End 処理フロー

```mermaid
sequenceDiagram
    actor User as 発注担当者
    participant Slack as Slack
    participant SC as Slackコネクタ(MCP)
    participant CW as Cowork
    participant FS as ローカルファイル
    participant Chrome as Claude in Chrome
    participant WA as WebシステムA
    participant WB as WebシステムB

    Note over Slack,WB: Phase 1: 自動検知・解析
    User->>Slack: #発注 チャネルにExcel投稿
    SC->>CW: 新規投稿を検知・トリガー
    CW->>FS: 添付Excelをダウンロード
    CW->>CW: Excel解析・バリデーション

    alt バリデーションエラー
        CW->>SC: Slackに差し戻し通知
        SC->>Slack: ❌ 「○○項目が未入力です」
    end

    Note over Slack,WB: Phase 2: 並列入力処理
    CW->>CW: 振り分けルール適用

    par システムA向け入力
        CW->>Chrome: サブエージェントA起動
        Chrome->>WA: ログイン→フォーム入力→送信
        Chrome->>CW: 入力完了・受注番号取得
    and システムB向け入力
        CW->>Chrome: サブエージェントB起動
        Chrome->>WB: ログイン→フォーム入力→送信
        Chrome->>CW: 入力完了・受注番号取得
    and 管理Excel更新
        CW->>FS: サブエージェントC起動
        FS->>FS: 管理Excelに新規行追加
    end

    Note over Slack,WB: Phase 3: 完了通知・レポート
    CW->>FS: 管理Excelにステータス・受注番号反映
    CW->>SC: 処理完了サマリをSlack送信
    SC->>Slack: ✅ 処理完了レポート投稿

    User->>Slack: 完了を確認（介入不要）
```

### 3.2 スキル（再利用可能ワークフロー）の設計

Coworkの「スキル」機能を使い、一度構築したワークフローを保存・再利用する。

```mermaid
flowchart TD
    subgraph "スキル: 受発注自動処理"
        S1["Step 1: Slack添付ファイル取得"]
        S2["Step 2: Excel解析\n・品目/数量/納期/発注先抽出\n・必須項目バリデーション"]
        S3["Step 3: 振り分けルール適用\n・発注先マスタ照合\n・システムA/B判定"]
        S4["Step 4: Chrome経由で\nWebシステムに自動入力"]
        S5["Step 5: 管理Excel更新\n・受注番号/ステータス記録\n・数式・条件付き書式維持"]
        S6["Step 6: Slack完了通知\n・処理サマリ\n・異常があれば詳細"]
    end

    S1 --> S2 --> S3 --> S4 --> S5 --> S6

    style S1 fill:#e3f2fd
    style S2 fill:#e3f2fd
    style S3 fill:#e3f2fd
    style S4 fill:#e3f2fd
    style S5 fill:#e3f2fd
    style S6 fill:#e3f2fd
```

> **スキルの利点**: 担当者が変わっても、同じスキルを呼び出すだけで同品質の処理が可能。属人化を完全に排除できる。

### 3.3 異常系のハンドリング

```mermaid
flowchart TD
    A["処理開始"] --> B{"Excel\nバリデーション"}
    B -->|"OK"| C{"振り分け\n判定可能？"}
    B -->|"NG: 必須項目不足"| E1["❌ Slack通知\n差し戻し依頼"]

    C -->|"OK"| D{"Webシステム\n入力成功？"}
    C -->|"NG: 不明な発注先"| E2["⚠️ Slack通知\n担当者に確認依頼"]

    D -->|"成功"| F["✅ 管理Excel更新\n完了通知"]
    D -->|"失敗: ログインエラー"| E3["🔴 Slack通知\nシステム障害報告"]
    D -->|"失敗: 入力エラー"| E4["🟡 Slack通知\nデータ不整合報告\n＋手動入力用データ添付"]

    E1 --> G["担当者が修正して再投稿"]
    E2 --> H["担当者が振り分け指示"]
    E3 --> I["システム復旧後に再実行"]
    E4 --> J["担当者が手動で修正入力"]

    G --> A
    H --> A
    I --> A

    style F fill:#c8e6c9
    style E1 fill:#ffcdd2
    style E2 fill:#fff9c4
    style E3 fill:#ffcdd2
    style E4 fill:#fff9c4
```

---

## 4. 受発注以外への横展開

Coworkの能力を受発注業務だけに閉じるのはもったいない。同じ仕組みで横展開できる業務を提案する。

```mermaid
mindmap
  root((Claude Cowork\n活用領域))
    受発注業務
      発注仕様書の自動処理
      ステータス管理の自動化
      納期アラート自動送信
    経理・請求
      請求書PDF → Excel取り込み
      経費精算レポート自動生成
      入金消込の照合支援
    レポーティング
      週次/月次レポート自動生成
      KPIダッシュボード更新
      会議資料の自動作成
    ナレッジ管理
      議事録からアクション抽出
      社内FAQ自動更新
      ドキュメント整理・分類
    顧客対応
      問い合わせ内容の分類・集計
      定型回答ドラフト生成
      対応履歴のExcel管理
```

### 横展開の優先度マトリクス

```mermaid
quadrantChart
    title 横展開の優先度（効果 × 導入容易性）
    x-axis "導入が難しい" --> "導入が容易"
    y-axis "効果が小さい" --> "効果が大きい"
    "受発注自動処理": [0.75, 0.9]
    "請求書取り込み": [0.8, 0.7]
    "週次レポート生成": [0.85, 0.6]
    "議事録アクション抽出": [0.9, 0.5]
    "経費精算レポート": [0.7, 0.55]
    "KPIダッシュボード": [0.5, 0.75]
    "問い合わせ分類": [0.4, 0.65]
    "入金消込照合": [0.35, 0.8]
```

---

## 5. 技術要件と準備事項

### 5.1 必要なコンポーネント

| コンポーネント | 用途 | 現在の状況 |
|-------------|------|----------|
| **Claude Desktop (macOS)** | Cowork実行環境 | 要確認 |
| **Maxプラン** | Cowork利用に必要 | 要契約 |
| **Slackコネクタ (MCP)** | Slack↔Cowork連携 | 設定が必要 |
| **Claude in Chrome** | Webシステム操作自動化 | 拡張機能インストール済み |
| **ローカルファイルアクセス** | Excel読み書き | 権限設定が必要 |

### 5.2 セキュリティ考慮事項

```mermaid
flowchart LR
    subgraph "信頼境界"
        CW["Cowork\n(VM内で実行)"]
        FS["許可されたフォルダ\nのみアクセス"]
    end

    subgraph "要注意ポイント"
        W1["Webシステムの\n認証情報管理"]
        W2["発注データの\n機密性"]
        W3["Coworkの\nアクション承認"]
    end

    subgraph "対策"
        M1["Chrome保存済み\nパスワードを利用"]
        M2["専用フォルダに\nスコープ限定"]
        M3["重要操作は\n確認モード"]
    end

    W1 --> M1
    W2 --> M2
    W3 --> M3
```

**推奨設定：**
- Coworkのファイルアクセスは `受発注専用フォルダ` のみに限定
- Claude in Chromeは「Ask before acting」モードで運用開始
- 本番Web入力は、まずステージング環境で十分に検証してから移行

---

## 6. 導入ロードマップ（見直し版）

```mermaid
gantt
    title Cowork中心のビジネスプロセス全体最適化ロードマップ
    dateFormat YYYY-MM-DD

    section Phase 0：環境構築
        Maxプラン契約・Claude Desktop導入        :p0a, 2025-01-01, 3d
        Slackコネクタ(MCP)設定                   :p0b, after p0a, 5d
        Claude in Chrome導入・権限設定            :p0c, after p0a, 5d
        受発注専用フォルダ構成整備                :p0d, after p0a, 3d

    section Phase 1：スキル開発
        振り分けルール・マスタデータ整備          :p1a, after p0d, 7d
        Excel解析スキル開発・テスト               :p1b, after p1a, 10d
        Webシステム入力スキル開発・テスト         :p1c, after p1b, 14d
        End-to-Endスキル統合テスト                :p1d, after p1c, 7d

    section Phase 2：パイロット運用
        少量案件で並行稼働（手動＋自動）          :p2a, after p1d, 14d
        精度・エラー率の検証                      :p2b, after p2a, 7d
        異常系ハンドリング調整                    :p2c, after p2b, 7d

    section Phase 3：本番移行
        全件Cowork経由に切り替え                  :p3a, after p2c, 14d
        運用手順書・スキルドキュメント整備        :p3b, after p2c, 7d
        担当者トレーニング                        :p3c, after p3b, 5d

    section Phase 4：横展開
        請求書処理の自動化                        :p4a, after p3a, 21d
        週次レポート自動生成                      :p4b, after p4a, 14d
        継続的改善・新スキル開発                   :p4c, after p4b, 30d
```

---

## 7. 期待される効果

### 定量的効果（推定）

| 指標 | 現状 | 前回提案 | 本提案 |
|------|------|---------|--------|
| 1件あたり処理時間 | 15〜30分 | 5〜10分 | **1〜3分**（確認のみ） |
| 担当者の関与度 | 100%手動 | 70%手動 | **10%（承認・例外対応のみ）** |
| 転記ミス発生率 | 月数件 | 大幅削減 | **ほぼゼロ** |
| 処理可能件数/日 | 15〜20件 | 30〜40件 | **100件以上** |
| 属人化リスク | 高 | 中 | **低（スキルで標準化）** |

### 定性的効果

```mermaid
graph LR
    A["担当者の時間創出"] --> B["戦略的業務への\nシフト"]
    C["ミス撲滅"] --> D["取引先からの\n信頼向上"]
    E["処理速度向上"] --> F["リードタイム短縮\n→ 競争力強化"]
    G["スキルによる標準化"] --> H["新人でも\n即戦力化"]
    I["横展開の基盤構築"] --> J["全社DXの\n加速"]

    style B fill:#c8e6c9
    style D fill:#c8e6c9
    style F fill:#c8e6c9
    style H fill:#c8e6c9
    style J fill:#c8e6c9
```

---

## 8. リスクと緩和策

| リスク | 影響度 | 発生可能性 | 緩和策 |
|--------|--------|-----------|--------|
| Webシステムの UI 変更で自動入力が失敗 | 高 | 中 | 定期的なスキル保守、異常検知→Slack即時通知 |
| Coworkのセッション切断（macOS スリープ等） | 中 | 中 | 処理中はスリープ抑制設定、中断時の自動リトライ |
| 機密データの意図しない露出 | 高 | 低 | フォルダスコープ限定、確認モード運用 |
| Maxプランのコスト（$200/月〜） | 中 | 確実 | 削減できる人件費・ミスコストとのROI比較 |
| Coworkがリサーチプレビュー段階 | 中 | 中 | Phase 2で十分な検証、手動フォールバック手順を維持 |

---

## 9. 次のアクション

1. **Maxプランの契約判断** — ROIシミュレーションをもとに経営判断
2. **Slackコネクタの設定** — MCP経由でSlackチャネルをCoworkに接続
3. **振り分けルールの棚卸し** — 現在の暗黙知をルールテーブルとして文書化
4. **PoC実施** — 5件程度の実案件でEnd-to-End処理を試行
5. **スキル化・標準化** — PoCで確立したワークフローをスキルとして保存
