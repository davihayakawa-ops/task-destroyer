# Task Destroyer MVP

Shopify商品ページ制作・広告制作・画像生成プロンプト・動画台本・SNS投稿を効率化し、
品質を統一するためのマーケティング支援ツール。

## 起動方法

### 1. 依存パッケージのインストール

```bash
cd core_studio
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を開き、`ANTHROPIC_API_KEY` に Anthropic API キーを設定してください。

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=claude-sonnet-4-6
```

### 3. 起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動で開きます。

---

## ディレクトリ構成

```
core_studio/
├── app.py                    # メインStreamlitアプリ
├── requirements.txt
├── .env.example
├── modules/                  # 共通モジュール
│   ├── llm_client.py         # Claude API ラッパー
│   ├── storage.py            # データ保存（JSON→Supabase移行可能）
│   ├── core_engine.py        # Core生成エンジン
│   ├── core_importer.py      # 外部Core取り込み
│   ├── translator.py         # 翻訳（PT⇔JA）
│   ├── japanese_refiner.py   # 日本語補正
│   ├── generator_engine.py   # コンテンツ生成エンジン
│   ├── exporter.py           # 出力・エクスポート
│   ├── checker.py            # 整合性・リスクチェック
│   ├── bulk_pack_generator.py # 一括生成パック
│   └── mode_registry.py      # モード管理
├── modes/
│   ├── commerce/             # Commerce Mode（Shopify特化）
│   └── custom/               # Custom Mode（将来拡張用）
├── data/                     # 保存データ（JSON）
├── i18n/                     # UI言語ファイル
│   ├── ja.json               # 日本語
│   └── pt.json               # ポルトガル語
└── prompts/                  # AIプロンプトテンプレート
```

---

## Phase 1 実装済み機能

- [x] モード選択（Commerce / Custom）
- [x] UI言語切り替え（日本語 / Português）
- [x] 商品情報入力・保存
- [x] Core作成方法選択（自動生成 / 外部取り込み / 再利用）
- [x] 商品情報からCore自動生成（Claude API）
- [x] 外部Core取り込み（ポルトガル語Core活用モード含む）
- [x] 言語自動判定
- [x] Core編集・保存・バージョン管理
- [x] 商品ページ生成
- [x] 画像生成プロンプト生成
- [x] 動画台本生成
- [x] 広告・SNS文生成
- [x] 一括生成パック（Shopify / 広告 / SNS / 画像 / 動画）
- [x] 日本語補正（10モード）
- [x] ポルトガル語→日本語変換
- [x] 日本語→ポルトガル語変換
- [x] 整合性チェック・リスク表現チェック
- [x] 作業ログ
- [x] Markdown / JSON / HTML 出力
- [x] 保存データ管理・プロジェクト読み込み
- [x] Custom Mode（自由入力・簡易版）

---

## Phase 2 TODO（次に実装すべき機能）

- [ ] 競合分析・市場分析（URLスクレイピング）
- [ ] Core品質チェック・補完
- [ ] Core比較・統合機能
- [ ] Coreライブラリ（全商品横断管理）
- [ ] ブランド辞書
- [ ] 勝ちパターン保存
- [ ] Shopify HTML出力（完全版）
- [ ] Shopify CSV出力
- [ ] 制作指示書出力
- [ ] 商品ジャンル別テンプレート
- [ ] NG表現・リスク表現の自動置き換え
- [ ] 商品ページ完成度スコア
- [ ] Shopify反映前チェック
- [ ] SEO補助機能

## Phase 3 TODO

- [ ] A/Bテスト案生成
- [ ] レビュー活用機能
- [ ] FAQ強化機能
- [ ] オファー設計機能

## Phase 4 TODO

- [ ] 商品ごとのプロジェクト管理（進行状況）
- [ ] 成果メモ機能
- [ ] 既存ページ改善提案
- [ ] 担当者管理・権限管理

## Phase 5 TODO（将来拡張）

- [ ] Custom Mode本格実装
- [ ] 別ジャンル追加（modes/新ジャンル/）
- [ ] Next.js化
- [x] Supabase Auth連携
- [x] 商品プロジェクトのSupabaseミラー保存
- [ ] 複数人運用

---

## 新しいジャンルの追加方法

1. `modes/新ジャンル名/` ディレクトリを作成
2. `modes/新ジャンル名/core_generator.py` を作成
3. `modules/mode_registry.py` の `MODES` に追加
4. `app.py` のルーターに追加

---

## 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `ANTHROPIC_API_KEY` | Anthropic APIキー | 必須 |
| `SUPABASE_URL` | SupabaseプロジェクトURL。設定時はSupabase Authを使用 | 未設定 |
| `SUPABASE_ANON_KEY` | Supabase anon key。`SUPABASE_URL` とセットで設定 | 未設定 |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase DB書き込み用のサーバー側キー。公開禁止 | 未設定 |
| `LLM_MODEL` | 使用するモデル | `claude-sonnet-4-6` |
| `APP_ENV` | `development` / `production`。本番では設定チェックが厳格化されます | `development` |
| `APP_BASE_URL` | パスワード再設定メールなどの戻り先URL | 未設定 |
| `DATA_DIR` | データ保存ディレクトリ | `data` |
| `TASK_DESTROYER_USERS` | ログインユーザーJSON。未設定時はローカル開発モード | 未設定 |
| `TASK_DESTROYER_MONTHLY_CALL_LIMIT` | ワークスペースごとの月間LLM呼び出し上限。`0`で無効 | `1000` |
| `TASK_DESTROYER_PLAN_LIMITS` | プラン別月間上限JSON。例: `{"free":100,"starter":500,"pro":2000}` | 内蔵デフォルト |
| `TASK_DESTROYER_TERMS_VERSION` | 利用規約・プライバシー同意のバージョン。変更すると再同意が必要 | `2026-05-18` |
| `STRIPE_SECRET_KEY` | Stripeサーバー側Secret Key | 未設定 |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook署名検証用Secret | 未設定 |
| `STRIPE_PRICE_PLAN_MAP` | Stripe Price IDとプラン名の対応JSON。例: `{"price_xxx":"pro"}` | 未設定 |
| `STRIPE_PLAN_PRICE_MAP` | プラン名とStripe Price IDの対応JSON。例: `{"pro":"price_xxx"}` | 未設定 |
| `BILLING_API_BASE_URL` | `billing_webhook.py` をデプロイしたAPIのベースURL | 未設定 |
| `BILLING_API_KEY` | Checkout作成API用のサーバー間認証キー | 未設定 |
| `STRIPE_SUCCESS_URL` | Checkout成功後の戻り先URL | `APP_BASE_URL?billing=success` |
| `STRIPE_CANCEL_URL` | Checkoutキャンセル後の戻り先URL | `APP_BASE_URL?billing=cancel` |

Supabase Authの確認メール/パスワード再設定メールは、開発中はSupabase標準メールでも動きます。一般販売で登録数が増える前に、SupabaseのSMTP Settingsで自社または契約メール送信サービスを設定してください。

## 本番公開前チェック

- `APP_ENV=production` を設定する
- `ANTHROPIC_API_KEY` は Streamlit Secrets などサーバー側Secretsに置く
- 一般販売では `SUPABASE_URL` と `SUPABASE_ANON_KEY` を設定し、Supabase Authを使う
- パスワード再設定を使う場合は `APP_BASE_URL` を公開URLに設定し、Supabase AuthのRedirect URLにも追加する
- DB保存へ移行する場合は `supabase_schema.sql` をSupabase SQL Editorで実行し、`SUPABASE_SERVICE_ROLE_KEY` をSecretsに設定する
- Supabase DBが設定済みの場合、商品プロジェクト、Core、関連生成物はJSON保存と並行してDBへミラー保存・復元されます
- Supabase DBが設定済みの場合、月間API使用量も`api_usage`へ保存されます
- Supabaseログイン後、`profiles`・`workspaces`・`workspace_members` は自動作成されます
- JSONログインを使う場合は `TASK_DESTROYER_USERS` を設定し、`password` ではなく `password_hash` を使う
- `TASK_DESTROYER_MONTHLY_CALL_LIMIT` を 1 以上にする
- Stripe課金を使う場合は `billing_webhook.py` をAPIとして別デプロイし、Webhook URLを `/stripe/webhook` に設定する
- アプリ内のアップグレード導線を使う場合は `BILLING_API_BASE_URL` と `BILLING_API_KEY` をStreamlit Secretsに設定する
- Checkout URL作成は `POST /stripe/checkout-session` を使い、`X-Billing-Api-Key` に `BILLING_API_KEY` を渡す
- Stripe Checkout作成時は `metadata.workspace_id` または `client_reference_id` にSupabaseのworkspace IDを入れる
- Stripe Checkout作成時は `metadata.plan` または `metadata.price_id` を入れ、`STRIPE_PRICE_PLAN_MAP` と一致させる
- 料金はStripeのPrice側で後から決められます。アプリ側には `STRIPE_PLAN_PRICE_MAP={"starter":"price_xxx","pro":"price_xxx","team":"price_xxx"}` のようにPrice ID対応を入れます
- `TASK_DESTROYER_TERMS_VERSION` を規約更新日などに合わせる
- `.env` や `.streamlit/secrets.toml` はGitにコミットしない
- 生成・削除・バックアップなどの運用ログは `data/.../audit_logs/` に保存されます

## Supabase設定の進め方

1. Supabaseで新しいプロジェクトを作る
2. Project Settings → API から `Project URL` と `anon public key` をコピーする
3. Project Settings → API から `service_role key` をコピーする。このキーは公開しない
4. Streamlit Secretsに `SUPABASE_URL`、`SUPABASE_ANON_KEY`、`SUPABASE_SERVICE_ROLE_KEY` を貼る
5. SupabaseのSQL Editorで `supabase_schema.sql` を全部実行する
6. Authentication → URL Configuration で、公開URLを Site URL と Redirect URLs に入れる
7. アプリを再起動して、新規登録・ログイン・商品保存・再ログイン後の復元を確認する

`service_role key` は管理者用の強いキーです。GitHub、画面、販売ページには出さず、Streamlit Secretsだけに保存してください。

## 販売前のユーザー分離テスト

一般販売前に、最低1回は下記を本番相当環境で確認してください。

1. Supabase AuthでテストユーザーAとBを作成する
2. Aでログインし、商品名に`A_ONLY_TEST`を含む商品を保存する
3. AでCore生成とShopifyコード生成を実行し、ログアウトする
4. Bでログインし、保存済み商品に`A_ONLY_TEST`が表示されないことを確認する
5. Bで商品名に`B_ONLY_TEST`を含む商品を保存し、ログアウトする
6. Aで再ログインし、`A_ONLY_TEST`だけが見えて`B_ONLY_TEST`が見えないことを確認する
7. Supabase SQL Editorで`products`、`cores`、`generated_contents`の`workspace_id`がユーザーごとに分かれていることを確認する

このテストが通れば、ログインユーザーごとの商品・Core・生成物が混ざらない基本動作を確認できます。
