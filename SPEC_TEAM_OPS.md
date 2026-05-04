# Task Destroyer チーム運用仕様書

バージョン: 0.1 (設計フェーズ)  
作成日: 2026-05-04  
ステータス: レビュー待ち・未実装

---

## 目次

1. [現状コード調査結果](#1-現状コード調査結果)
2. [保存データ構造と保護方針](#2-保存データ構造と保護方針)
3. [役割一覧（Role）](#3-役割一覧role)
4. [ページ許可リスト](#4-ページ許可リスト)
5. [操作許可リスト](#5-操作許可リスト)
6. [承認フロー](#6-承認フロー)
7. [翻訳フロー](#7-翻訳フロー)
8. [UI言語と生成物言語の分離ルール](#8-ui言語と生成物言語の分離ルール)
9. [保存データ構造案（拡張後）](#9-保存データ構造案拡張後)
10. [API使用ガード](#10-api使用ガード)
11. [権限チェック関数の設計案](#11-権限チェック関数の設計案)
12. [触る必要があるファイル](#12-触る必要があるファイル)
13. [触ると危険な処理](#13-触ると危険な処理)
14. [安全な実装順序](#14-安全な実装順序)
15. [開発用 role 仮切り替え設計](#15-開発用-role-仮切り替え設計)
16. [将来のGoogleログイン方針](#16-将来のgoogleログイン方針)
17. [将来追加予定の役割](#17-将来追加予定の役割)
18. [ステータス一覧](#18-ステータス一覧)

---

## 1. 現状コード調査結果

### 1-1. ファイル構成

```
core_studio/
├── app.py                    # メインアプリ (4,685行)
├── data/
│   ├── projects/             # 商品メタデータ + 生成コンテンツ
│   ├── core_library/         # Core テキスト（バージョン管理）
│   ├── approvals/            # コンテンツ種別ごとの承認状態
│   ├── activity_logs/        # JSONL 監査ログ
│   ├── delete_logs/          # 削除記録
│   ├── backups/              # ZIP バックアップ
│   ├── trash/                # ソフト削除済み商品
│   ├── ab_tests/
│   ├── bulk_packs/
│   ├── reviews/
│   ├── performance_notes/
│   └── category_templates/
├── modules/
│   ├── storage.py            # データ永続化層 (603行)
│   ├── generator_engine.py   # コンテンツ生成 (829行)
│   ├── core_engine.py
│   ├── approval_flow.py
│   ├── translator.py
│   ├── llm_client.py
│   ├── exporter.py
│   └── ...
├── i18n/                     # 日本語/Português 翻訳ファイル
└── prompts/
```

### 1-2. ページ関数一覧（app.py）

| 関数名 | 行数 | 説明 |
|--------|------|------|
| `page_new_dashboard` | — | ホームダッシュボード |
| `page_mode_selection` | — | モード選択 |
| `page_product_input` | ~871 | 商品情報入力 |
| `page_external_core` | — | Core インポート |
| `page_core_generation` | ~1227 | Core 生成・編集 |
| `page_product_page` | ~1533 | 商品ページ生成 |
| `page_image_prompt` | ~2068 | 画像プロンプト生成 |
| `page_video_script` | ~2155 | 動画台本生成 |
| `page_ads_sns` | ~2240 | 広告・SNS 生成 |
| `page_bulk_pack` | — | 一括生成 |
| `page_refinement` | — | 校正・リファイン |
| `page_check` | — | チェック |
| `page_approval` | ~2583 | 承認フロー |
| `page_output` | — | 出力 |
| `page_saved_data` | ~3454 | 保存データ管理 |
| `page_export_center` | — | エクスポートセンター |
| `page_instruction_sheet` | — | 作業指示書 |

### 1-3. 主要セッション変数

| キー | 型 | 内容 |
|------|----|------|
| `lang` | str | "ja" または "pt" |
| `page` | str | 現在のページID |
| `product_id` | str | 現在の商品UUID[:8] |
| `product_info` | dict | 商品メタデータ |
| `core_text` | str | 生成済みCore本文 |
| `core_status` | str | "draft" / "ai_generated" / "edited" |
| `generated` | dict | content_type → テキスト |
| `approval` | dict | 承認状態キャッシュ |
| `assignee` | str | 担当者 |
| `reviewer` | str | 最終確認者 |

### 1-4. Storage の主要メソッドとパス

| メソッド | 保存パス | 備考 |
|----------|----------|------|
| `save_product(pid, data)` | `data/projects/{pid}.json` | 商品メタデータ |
| `load_product(pid)` | `data/projects/{pid}.json` | — |
| `list_products()` | `data/projects/*.json` | `_`始まりファイルを除外 |
| `save_core(pid, data, label)` | `data/core_library/{pid}_{cid}.json` | バージョン管理 |
| `load_latest_core(pid)` | `data/core_library/` | 最新バージョン |
| `save_generated(pid, type, data)` | `data/projects/{pid}_{type}_{id}.json` | 生成コンテンツ |
| `load_generated(pid, type)` | `data/projects/` | 最新の生成物 |
| `update_approval(pid, type, status)` | `data/approvals/{pid}_{type}.json` | — |
| `log_activity(pid, action, detail, user)` | `data/activity_logs/{pid}.jsonl` | 追記型 |
| `delete_project(pid, ..., use_trash=True)` | → `data/trash/` | ゴミ箱方式 |
| `create_backup(label)` | `data/backups/*.zip` | ZIP一括 |
| `list_trash()` | `data/trash/` | — |
| `restore_from_trash(filename)` | → 元のパスへ復元 | — |
| `get_diagnostics()` | 全ディレクトリをスキャン | 診断のみ・変更なし |

### 1-5. DATA_DIR の解決方法

```python
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = Path(__file__).resolve().parent.parent / DATA_DIR
# → /Users/hayakawa/Desktop/core_studio/data/
```

環境変数 `DATA_DIR` で上書き可能。絶対パスが設定されていない場合はプロジェクトルート基準。

---

## 2. 保存データ構造と保護方針

### 2-1. 現在の保存データの場所

| フォルダ | 内容 | 重要度 |
|----------|------|--------|
| `data/projects/` | 商品ファイル + 生成コンテンツファイル | ★★★ 最重要 |
| `data/core_library/` | Core テキスト全バージョン | ★★★ 最重要 |
| `data/approvals/` | 承認状態 | ★★★ 最重要 |
| `data/activity_logs/` | 操作ログ（JSONL） | ★★ 重要 |
| `data/delete_logs/` | 削除記録 | ★★ 重要 |
| `data/trash/` | ソフト削除済みデータ | ★★ 重要 |
| `data/backups/` | ZIP バックアップ | ★★ 重要 |
| `data/ab_tests/` | A/B テスト記録 | ★ |
| `data/bulk_packs/` | 一括生成結果 | ★ |
| `data/reviews/` | レビュー記録 | ★ |
| `data/performance_notes/` | パフォーマンスメモ | ★ |
| `data/category_templates/` | カテゴリテンプレート | ★ |

### 2-2. 保存ファイルの命名規則

```
data/projects/
  {pid}.json                         # 商品メタデータ本体
  {pid}_{content_type}_{id}.json     # 生成コンテンツ（projects/内に混在）

data/core_library/
  {pid}_{core_id[:8]}.json           # Coreバージョン

data/approvals/
  {pid}_{content_type}.json          # 承認状態

data/activity_logs/
  {pid}.jsonl                        # 操作ログ（追記型）

data/trash/
  {pid}_deleted_{YYYYMMDD_HHMMSS}.json  # ゴミ箱
```

**重要な注意点:**
- `data/projects/` には商品ファイルと生成コンテンツファイルが**混在**している
- `list_products()` は `content_type` キーを持つファイルを除外して商品のみ返す
- `_` 始まりのstemを持つファイルは `list_products()` が除外する

### 2-3. 保存データのキー（現状 projects/{pid}.json）

```json
{
  "name": "商品名",
  "category": "カテゴリ",
  "product_url": "URL",
  "description": "説明文",
  "price": "価格",
  "target": "ターゲット",
  "features": "特徴",
  "brand_tone": "ブランドトーン",
  "assignee": "担当者",
  "final_reviewer": "確認者",
  "updated_at": "2025-XX-XX XX:XX:XX"
}
```

### 2-4. 権限管理追加後の拡張フィールド（追加予定）

以下は権限管理フェーズで追加予定のフィールド。
**古いデータにこれらがなくても落ちないよう、すべてデフォルト値で補完する。**

```json
{
  "created_by": "",
  "assigned_to": "",
  "current_status": "商品準備中",
  "next_owner": "",
  "priority": "normal",
  "due_date": "",

  "input_original_language": "pt",
  "input_original": {},
  "input_ja": {},
  "translation_status": "not_translated",
  "translated_at": "",
  "translated_by": "",

  "product_prep_approved": false,
  "product_prep_approved_by": "",
  "product_prep_approved_at": "",
  "product_prep_approval_note": "",

  "core_approved": false,
  "core_approved_by": "",
  "core_approved_at": "",

  "workflow_logs": [],
  "permissions_version": 1
}
```

### 2-5. 古いデータでも落ちないようにするルール

```python
# 権限フィールドのデフォルト補完（storage.py または app.py のload時）
_PERMISSION_DEFAULTS = {
    "created_by": "",
    "product_prep_approved": False,
    "product_prep_approved_by": "",
    "product_prep_approved_at": "",
    "product_prep_approval_note": "",
    "core_approved": False,
    "input_original_language": "ja",
    "input_original": {},
    "input_ja": {},
    "translation_status": "not_translated",
    "current_status": "商品準備中",
    "permissions_version": 0,
}

def _fill_defaults(data: dict) -> dict:
    for key, default in _PERMISSION_DEFAULTS.items():
        if key not in data:
            data[key] = default
    return data
```

`load_product()` の返値に `_fill_defaults()` を通すか、  
`_load_project_session()` でセッションに入れる前に補完する。  
どちらか一箇所でよい（二重補完は不要）。

### 2-6. バックアップ方針

**バックアップ前に必ず確認すべきフォルダ（最重要3つ）:**
1. `data/projects/`
2. `data/core_library/`
3. `data/approvals/`

**自動バックアップを必ず実行すべき操作:**
- 空プロジェクト一括削除の前
- データ構造変更（フィールド追加）の前
- 権限管理機能追加の前
- 翻訳フィールド構造変更の前
- ZIPからのリストア前

**バックアップZIPに含めてはいけないもの:**
- `.env`
- `.streamlit/secrets.toml`
- `secret*` パターンのファイル
- APIキー・認証情報を含むすべてのファイル

**バックアップZIPのファイル名:**
```
task_destroyer_backup_YYYYMMDD_HHMMSS.zip   # 手動
backup_before_{label}_YYYYMMDD_HHMMSS.zip   # 自動（操作前）
```

### 2-7. ゴミ箱方式削除の方針

`delete_project()` のデフォルト: `use_trash=True`（既に実装済み）

```
削除操作
  ↓
data/projects/{pid}.json
  ↓ 移動（unlink しない）
data/trash/{pid}_deleted_YYYYMMDD_HHMMSS.json
  + _trash_meta: { product_id, original_path, deleted_at, deleted_by, reason }
```

- 関連ファイル（Core、生成コンテンツ、承認、ログ）は移動しない  
- 復元時は `_trash_meta.original_path` に戻す  
- ゴミ箱内のファイルは永久削除操作が来るまで保持  

### 2-8. 実装前に必ずやること（チェックリスト）

```
[ ] data/projects/ の全ファイルをZIPバックアップ
[ ] data/core_library/ の全ファイルをZIPバックアップ
[ ] data/approvals/ の全ファイルをZIPバックアップ
[ ] バックアップZIPをローカルPCにダウンロードして保管
[ ] git commit（コード変更前の状態をコミット）
[ ] app.py のバックアップコピーを作成（app.py.bak_YYYYMMDD）
```

---

## 3. 役割一覧（Role）

### 3-1. 今回実装対象の役割

| role | 対象者 | 説明 |
|------|--------|------|
| `admin` | Davi, Sara | 全権限。承認・削除・Core生成・全ページアクセス |
| `product_researcher` | Iago | 商品準備入力のみ。Core生成・承認・削除は不可 |
| `viewer` | 未登録ユーザー | アプリ本体を表示しない |

### 3-2. admin の権限

- 全ページ閲覧・操作
- 商品準備承認 / 差し戻し
- Core生成 / Core編集 / Core承認
- Shopifyコード生成
- 画像プロンプト生成
- 動画台本生成
- 広告・SNS生成
- 保存データ管理（一覧・読み込み・削除）
- バックアップ作成・リストア
- 翻訳実行（Português → 日本語）
- 最終承認

### 3-3. product_researcher (Iago) の権限

**できること:**
- 商品情報をPortuguêsで入力
- 商品URL / 価格 / カテゴリ / ターゲット入力
- 商品準備メモ入力
- 参考URL / 競合URL入力
- 保存（下書き）
- 「商品準備完了」ボタンを押してステータス変更

**できないこと:**
- Core生成・Core編集・Core承認
- 商品準備承認・差し戻し
- Shopifyコード生成
- 画像プロンプト生成
- 動画台本生成
- 広告・SNS生成
- 削除
- バックアップ・リストア
- 最終承認
- 翻訳実行

### 3-4. viewer の扱い

- アプリ本体のコンテンツを表示しない
- 「このアカウントにはアクセス権限がありません。管理者に連絡してください。」と表示
- セッション変数に何も書き込まない

---

## 4. ページ許可リスト

### admin（表示可能: 全ページ）

```
✅ ホームダッシュボード
✅ 商品入力
✅ Core生成・編集
✅ Core外部インポート
✅ 商品ページ生成
✅ Shopifyコード生成
✅ 画像プロンプト生成
✅ 動画台本生成
✅ 広告・SNS生成
✅ 一括生成
✅ 校正・リファイン
✅ チェック
✅ 承認フロー
✅ 出力
✅ 保存データ管理
✅ エクスポートセンター
✅ 作業指示書
```

### product_researcher / Iago（表示可能: 限定）

```
✅ ホームダッシュボード（自分の担当商品のみ）
✅ 商品入力（商品準備フィールドのみ）
✅ 保存（自分が担当している商品のみ）
❌ Core生成・編集
❌ Core外部インポート
❌ 商品ページ生成
❌ Shopifyコード生成
❌ 画像プロンプト生成
❌ 動画台本生成
❌ 広告・SNS生成
❌ 一括生成
❌ 校正・リファイン
❌ チェック
❌ 承認フロー
❌ 出力
❌ 保存データ管理（削除・バックアップ不可）
❌ エクスポートセンター
❌ 作業指示書
```

### viewer

```
❌ 全ページ非表示
⚠️ アクセス権限なしメッセージのみ表示
```

---

## 5. 操作許可リスト

### admin

| 操作 | 許可 |
|------|------|
| 保存（全商品） | ✅ |
| 読み込み（全商品） | ✅ |
| 削除（ゴミ箱方式） | ✅ |
| 商品準備承認 | ✅ |
| 商品準備差し戻し | ✅ |
| Core生成 | ✅（要: product_prep_approved == true） |
| Core編集 | ✅ |
| Core承認 | ✅ |
| Shopifyコード生成 | ✅ |
| 画像プロンプト生成 | ✅ |
| 動画台本生成 | ✅ |
| 広告・SNS生成 | ✅ |
| 翻訳実行（PT→JA） | ✅ |
| バックアップ作成 | ✅ |
| バックアップからリストア | ✅ |
| ゴミ箱から復元 | ✅ |
| 永久削除 | ✅ |
| 最終承認 | ✅ |

### product_researcher / Iago

| 操作 | 許可 |
|------|------|
| 商品情報入力 | ✅（Português） |
| 商品準備メモ入力 | ✅ |
| 参考URL入力 | ✅ |
| 競合URL入力 | ✅ |
| 保存（自分の担当商品） | ✅ |
| 商品準備完了にする | ✅ |
| Core生成 | ❌ |
| 商品準備承認 | ❌ |
| Core承認 | ❌ |
| Shopifyコード生成 | ❌ |
| 画像プロンプト生成 | ❌ |
| 動画台本生成 | ❌ |
| 広告・SNS生成 | ❌ |
| 削除 | ❌ |
| バックアップ・リストア | ❌ |
| 翻訳実行 | ❌ |

### viewer

| 操作 | 許可 |
|------|------|
| 全操作 | ❌ |

---

## 6. 承認フロー

### 6-1. 全体フロー

```
Step 1: Iagoが商品情報をPortuguêsで入力
         → ステータス: 「商品準備中」
         → created_by: "iago"
         → input_original_language: "pt"

Step 2: Iagoが「商品準備完了」ボタンを押す
         → ステータス: 「Davi確認待ち」
         → product_prep_approved: false

Step 3: DaviまたはSaraが商品情報を確認
         → 必要なら「日本語に変換」ボタンで input_ja を生成
         → 原文（input_original）は上書きしない

Step 4a: 問題なければ「商品準備承認」
         → product_prep_approved: true
         → product_prep_approved_by: "davi" または "sara"
         → product_prep_approved_at: タイムスタンプ
         → ステータス: 「承認済み / Core生成可能」

Step 4b: 問題があれば「差し戻し」
         → ステータス: 「差し戻し」
         → product_prep_approval_note: 差し戻しコメント（翻訳対象）
         → Iagoに修正を促す

Step 5: DaviまたはSaraがCore生成
         → 条件: role == "admin" かつ product_prep_approved == true
         → 条件を満たさない場合はAPIを呼ばない
         → ステータス: 「Core作成中」

Step 6: Core生成完了
         → ステータス: 「Core確認待ち」

Step 7: SaraがShopifyページ・画像・動画作成
         → ステータス: 「ページ作成中」 → 「画像・動画作成中」

Step 8: DaviがSNS運用・最終確認
         → ステータス: 「SNS素材作成中」 → 「投稿準備完了」 → 「完了」
```

### 6-2. Core生成ゲート（二重チェック）

```
UIレベル: Core生成ボタンを disabled（条件未満の時）
          「管理者の承認が完了するまでCore生成はできません」を表示

処理レベル: API呼び出し直前に必ず以下をチェック
  if role != "admin":
      raise PermissionError("Core生成権限がありません")
  if not project.get("product_prep_approved"):
      raise PermissionError("商品準備が承認されていません")
```

**重要:** UIでボタンを隠すだけでは不十分。処理直前にも必ずチェックすること。

---

## 7. 翻訳フロー

### 7-1. 基本方針

- Iagoが触るUIはPortuguês表示
- 入力内容はPortuguês原文のまま保存（`input_original` に格納）
- DaviまたはSaraが確認する時だけ「日本語に変換」ボタンで `input_ja` を生成
- 保存ボタンを押しただけでは自動翻訳しない
- UI言語を切り替えただけでは自動翻訳しない
- 原文（`input_original`）は絶対に上書きしない

### 7-2. 翻訳対象フィールド

| フィールド | 翻訳対象 |
|-----------|---------|
| 商品情報（name, description等） | ✅ |
| 商品説明 | ✅ |
| 商品準備メモ | ✅ |
| 競合分析メモ | ✅ |
| レビュー分析メモ | ✅ |
| 差別化ポイント | ✅ |
| 参考素材メモ | ✅ |
| 広告素材メモ | ✅ |
| 差し戻しコメント | ✅ |

### 7-3. 翻訳してはいけないもの

| コンテンツ | 翻訳禁止理由 |
|-----------|------------|
| Core本文 | 確定済みブランド戦略テキスト |
| Shopifyコード | HTMLコードを壊す可能性 |
| 画像プロンプト | AI生成指示文 |
| 動画台本 | 確定済み台本 |
| 広告SNS文 | 確定済み投稿文 |
| 承認済みコンテンツ全般 | 変更不可 |
| 保存済み生成物 | 変更不可 |

### 7-4. 翻訳データ構造

```json
{
  "input_original_language": "pt",
  "input_original": {
    "name": "Nome do produto",
    "description": "Descrição completa...",
    "memo": "Notas sobre o produto..."
  },
  "input_ja": {
    "name": "商品名",
    "description": "商品説明...",
    "memo": "商品メモ..."
  },
  "translation_status": "translated",
  "translated_at": "2026-05-04 12:00:00",
  "translated_by": "davi"
}
```

---

## 8. UI言語と生成物言語の分離ルール

### 8-1. UI言語（切り替えてよいもの）

```
メニュー名
ボタンラベル
入力フォームのラベル
プレースホルダー
説明文・ヘルプテキスト
ステータス表示
エラーメッセージ
タブ名
サイドバーナビゲーション
承認フローのラベル
```

→ `i18n/ja.json` と `i18n/pt.json` で管理。`st.session_state.lang` で切り替え。

### 8-2. 生成物言語（UI言語を切り替えても変えてはいけないもの）

```
Core本文
商品ページ本文
Shopifyコード（HTML/CSS/JavaScript）
画像プロンプト
動画台本
広告SNS文
保存済み生成物全般
```

→ 生成物はファイルに保存された内容をそのまま表示する。  
→ UIの言語切り替えは表示ラベルのみに影響し、保存データには一切影響しない。

### 8-3. 実装ルール（コード規約）

```python
# ✅ 正しい: UIラベルはi18nを使う
st.button(t("core.generate_button"))

# ✅ 正しい: 生成物はそのまま表示
st.text_area("Core", value=st.session_state.core_text)

# ❌ 禁止: 生成物にt()を通す
st.text_area(t("core.label"), value=t(st.session_state.core_text))  # 禁止

# ❌ 禁止: lang変更時に生成物を自動翻訳
if lang_changed:
    st.session_state.core_text = translate(st.session_state.core_text)  # 禁止
```

---

## 9. 保存データ構造案（拡張後）

`data/projects/{pid}.json` の推奨フル構造：

```json
{
  "name": "商品名",
  "category": "カテゴリ",
  "product_url": "https://...",
  "description": "説明",
  "price": "価格",
  "target": "ターゲット",
  "features": "特徴",
  "brand_tone": "ブランドトーン",
  "assignee": "iago",
  "final_reviewer": "davi",
  "updated_at": "2026-05-04 12:00:00",

  "created_by": "iago",
  "assigned_to": "iago",
  "current_status": "Davi確認待ち",
  "next_owner": "davi",
  "priority": "normal",
  "due_date": "",

  "input_original_language": "pt",
  "input_original": {
    "name": "Nome do produto",
    "description": "Descrição...",
    "memo": "Notas..."
  },
  "input_ja": {
    "name": "商品名",
    "description": "商品説明...",
    "memo": "商品メモ..."
  },
  "translation_status": "translated",
  "translated_at": "2026-05-04 13:00:00",
  "translated_by": "davi",

  "product_prep_approved": true,
  "product_prep_approved_by": "davi",
  "product_prep_approved_at": "2026-05-04 14:00:00",
  "product_prep_approval_note": "",

  "core_approved": false,
  "core_approved_by": "",
  "core_approved_at": "",

  "workflow_logs": [
    {"timestamp": "2026-05-04 12:00:00", "action": "created", "by": "iago"},
    {"timestamp": "2026-05-04 12:30:00", "action": "submitted_for_review", "by": "iago"},
    {"timestamp": "2026-05-04 14:00:00", "action": "product_prep_approved", "by": "davi"}
  ],

  "permissions_version": 1
}
```

### 9-1. デフォルト補完の必須項目

古い保存データに以下がなくても `load_product()` 時に補完する:

| フィールド | デフォルト値 |
|-----------|------------|
| `created_by` | `""` |
| `product_prep_approved` | `false` |
| `product_prep_approved_by` | `""` |
| `product_prep_approved_at` | `""` |
| `product_prep_approval_note` | `""` |
| `core_approved` | `false` |
| `input_original_language` | `"ja"` |
| `input_original` | `{}` |
| `input_ja` | `{}` |
| `translation_status` | `"not_translated"` |
| `current_status` | `"商品準備中"` |
| `workflow_logs` | `[]` |
| `permissions_version` | `0` |

---

## 10. API使用ガード

### 10-1. Core生成前ガード

```python
def _guard_core_generation(role: str, project: dict):
    if role != "admin":
        st.error("Core生成には管理者権限が必要です。")
        st.stop()
    if not project.get("product_prep_approved"):
        st.error("管理者の承認が完了するまでCore生成はできません。")
        st.stop()
    if not project.get("name", "").strip():
        st.error("商品情報が入力されていません。")
        st.stop()
```

### 10-2. 生成系全般ガード

| チェック項目 | 対応 |
|------------|------|
| role != admin | API呼ばない + エラー表示 |
| product_prep_approved == false | API呼ばない + メッセージ表示 |
| core_text が空 | API呼ばない + メッセージ表示 |
| 選択項目なし（チェックボックス） | API呼ばない + メッセージ表示 |
| クレジット不足 | 分かりやすいエラーUI表示 |

### 10-3. APIエラー文を保存データに含めない

以下のパターンがAPIレスポンスに含まれていた場合、保存しない・表示のみ:

```python
_ERROR_PATTERNS = [
    "Your credit balance is too low",
    "Anthropic APIエラー",
    "invalid_request_error",
    "Error code: 400",
    "Error code: 529",
    "overloaded_error",
]

def _is_api_error(text: str) -> bool:
    return any(p in text for p in _ERROR_PATTERNS)

# 生成結果をsave前に必ずチェック
if _is_api_error(result):
    st.error(f"APIエラーが発生しました。保存しません。\n{result}")
    return  # save_generated() を呼ばない
```

---

## 11. 権限チェック関数の設計案

### 11-1. 関数一覧

```python
# modules/permissions.py （新規作成予定）

def get_current_role() -> str:
    """
    開発フェーズ: st.session_state.dev_role から取得
    本番フェーズ: st.user.email → USER_ROLES dict でlookup
    未登録: "viewer" を返す
    """
    ...

def can_view_page(role: str, page_name: str) -> bool:
    """ページ表示許可チェック"""
    ...

def can_perform_action(role: str, action_name: str) -> bool:
    """操作許可チェック"""
    ...

def can_approve_product_prep(role: str) -> bool:
    return role == "admin"

def can_generate_core(role: str, project: dict) -> bool:
    return role == "admin" and project.get("product_prep_approved", False)

def can_edit_core(role: str) -> bool:
    return role == "admin"

def can_generate_shopify(role: str, project: dict) -> bool:
    return role == "admin"

def can_generate_creative(role: str, project: dict) -> bool:
    return role == "admin"

def can_delete_project(role: str) -> bool:
    return role == "admin"

def require_permission(role: str, action_name: str):
    """
    権限がない場合は st.error() + st.stop() で処理停止
    UIブロックとは別に、処理実行直前でも呼ぶ
    """
    if not can_perform_action(role, action_name):
        st.error(f"この操作を行う権限がありません: {action_name}")
        st.stop()
```

### 11-2. ページ許可マップ

```python
# modules/permissions.py

PAGE_PERMISSIONS = {
    "admin": "__all__",
    "product_researcher": [
        "page_new_dashboard",
        "page_product_input",
    ],
    "viewer": [],
}

ACTION_PERMISSIONS = {
    "admin": "__all__",
    "product_researcher": [
        "save_product",
        "submit_product_prep",
        "input_product_info",
    ],
    "viewer": [],
}
```

### 11-3. 二重ガードの原則

```
[ UI層 ]
  ↓ ボタンを disabled にする / ページを非表示にする

[ 処理層 ]
  ↓ require_permission() を直前で呼ぶ
  ↓ API呼び出し直前にも role + approval チェック

理由: UIのみでガードすると、
　　  セッション操作やバグで通り抜けるリスクがある
```

---

## 12. 触る必要があるファイル

### 必ず触るファイル

| ファイル | 理由 |
|---------|------|
| `app.py` | role切り替えUI追加、ページ表示制御、ボタン制御、承認ゲート |
| `modules/storage.py` | デフォルト補完追加（`_fill_defaults`）、承認フィールド保存/読み込み |

### 新規作成するファイル

| ファイル | 理由 |
|---------|------|
| `modules/permissions.py` | 権限チェック関数を集約する新モジュール |
| `i18n/pt.json` への追記 | Iago向けPortuguêsラベル |
| `i18n/ja.json` への追記 | 新規ステータス・ラベルの追加 |

### 触らなくてよいファイル（慎重に避ける）

| ファイル | 理由 |
|---------|------|
| `modules/generator_engine.py` | 生成ロジックは変更しない |
| `modules/llm_client.py` | API接続は変更しない |
| `modules/translator.py` | 翻訳ロジックは変更しない |
| `modules/approval_flow.py` | 既存承認フローを壊さない |
| `modules/exporter.py` | 出力ロジックは変更しない |
| `data/` 以下 | コードで操作。直接編集しない |

---

## 13. 触ると危険な処理

### ★★★ 絶対に慎重に扱う処理

| 処理 | 危険な理由 | 対応方針 |
|------|-----------|---------|
| `delete_project()` | 保存データ消失 | use_trash=True を強制維持 |
| `restore_from_backup()` | 既存データ上書き | 必ずpre_backup自動作成 |
| `purge_trash()` | 永久削除・復元不可 | 確認ダイアログ必須 |
| `list_products()` の除外ロジック | 変更でデータが見えなくなる | 触らない |
| `_load_project_session()` | セッション上書き | デフォルト補完のみ追加 |

### ★★ 変更に注意が必要な処理

| 処理 | 注意理由 |
|------|---------|
| `save_product()` | フィールドを誤って削除しないよう merge する |
| `save_generated()` | ファイル命名規則を変えると既存データが読めなくなる |
| サイドバーUI | ページ遷移ロジックを壊すと全ページにアクセス不可 |
| `init_state()` | セッション初期化ロジックを変えると全機能に影響 |
| `get_services()` | `@st.cache_resource` が外れると毎回インスタンス作成 |

### ★ 慎重に進める処理

| 処理 | 注意理由 |
|------|---------|
| i18nファイル追記 | 既存キーを削除・変更しない |
| `page_approval()` | 既存の承認ロジックを壊さない |
| `page_product_input()` | フィールド追加は append のみ |

---

## 14. 安全な実装順序

### Phase 0: 保存データの確認・バックアップ（今すぐ実行推奨）

```
[ ] 現在の data/ 全体をバックアップ ZIP に保存
[ ] バックアップをローカルPCにダウンロード
[ ] data/projects/ にファイルが何件あるか確認
[ ] data/core_library/ にファイルが何件あるか確認
[ ] サンプルファイルを1件開いて構造を目視確認
[ ] git commit (現状コードをコミット)
```

### Phase 1: 仕様書確定・準備（今回）

```
[ ] 本仕様書のレビュー・修正
[ ] ページ許可リスト最終確認
[ ] 操作許可リスト最終確認
[ ] i18n追加キーのリストアップ
[ ] DaviのOK取得 → Phase 2 開始
```

### Phase 2: 開発用 role 仮切り替え

```
[ ] modules/permissions.py 新規作成
    - PAGE_PERMISSIONS, ACTION_PERMISSIONS 定義
    - get_current_role(), can_view_page(), can_perform_action() 実装
[ ] app.py: サイドバーに role 仮切り替えセレクトボックス追加
    - Davi (admin) / Sara (admin) / Iago (product_researcher) / viewer
[ ] app.py: メインルーターに can_view_page() チェック追加
[ ] app.py: viewer の場合はアクセス権限なしメッセージ表示
[ ] 動作確認: 各roleで表示ページが正しく制御されているか
[ ] 動作確認: 既存機能が壊れていないか
```

### Phase 3: 承認ゲート

```
[ ] storage.py: _fill_defaults() 追加
[ ] storage.py: load_product() の返値に _fill_defaults() 適用
[ ] app.py: _load_project_session() でデフォルト補完を確認
[ ] app.py: can_generate_core() チェックを Core生成ボタンに追加
[ ] app.py: Core生成処理直前にも require_permission() 追加
[ ] app.py: 承認状態表示UI（product_prep_approved バッジ）追加
[ ] app.py: admin向け「商品準備承認」「差し戻し」ボタン追加
[ ] 動作確認: 未承認でCore生成ボタンが disabled になるか
[ ] 動作確認: 承認後にCore生成ボタンが有効になるか
[ ] 動作確認: 既存の承認フローが壊れていないか
```

### Phase 4: Português入力と日本語確認

```
[ ] storage.py: input_original, input_ja フィールドの保存・読み込み
[ ] app.py: Iago向け商品入力UIをPortuguês表示に切り替え
[ ] app.py: 「日本語に変換」ボタン（admin専用）追加
[ ] app.py: 翻訳結果を input_ja に保存（input_original は上書きしない）
[ ] i18n/pt.json: Iago向けラベル追加
[ ] 動作確認: Iago roleでPortuguês入力が正常に保存されるか
[ ] 動作確認: admin roleで日本語変換ボタンが動作するか
[ ] 動作確認: 既存データが壊れていないか
```

### Phase 5: 画像・動画・SNS 選択式生成（既に実装済み）

```
[ ] 既実装の動作確認
[ ] role チェックを追加（admin 専用）
[ ] APIエラーガードの確認
```

### Phase 6: 保存データバックアップ・ゴミ箱・復元（既に実装済み）

```
[ ] 既実装の動作確認
[ ] バックアップ画面の動作テスト
[ ] ゴミ箱からの復元テスト
[ ] 永久削除の確認ダイアログテスト
```

### Phase 7: Googleログイン（将来・今回対象外）

```
[ ] st.user.email の取得
[ ] USER_ROLES dict でのrole判定
[ ] 未登録メールは viewer 扱い
[ ] 開発用 role 仮切り替えを削除
```

### Phase 8: UIデザイン統一（将来）

```
[ ] Iago向けPT UIの視覚的統一
[ ] ステータス表示の統一
[ ] モバイル対応確認
```

---

## 15. 開発用 role 仮切り替え設計

### サイドバーへの追加箇所

app.py の `render_sidebar()` 内、言語切り替えボタンの直下に追加。

```python
# サイドバー: 開発用 role 仮切り替え
st.markdown("---")
st.caption("🔧 開発用 / Dev mode")
dev_role_options = {
    "Davi (admin)": ("davi", "admin"),
    "Sara (admin)": ("sara", "admin"),
    "Iago (product_researcher)": ("iago", "product_researcher"),
    "viewer": ("", "viewer"),
}
selected = st.selectbox(
    "役割切り替え",
    options=list(dev_role_options.keys()),
    key="dev_role_selector",
)
dev_user, dev_role = dev_role_options[selected]
st.session_state.dev_user = dev_user
st.session_state.dev_role = dev_role
```

### get_current_role() の実装方針

```python
def get_current_role() -> str:
    # フェーズ2（開発用）: session_stateから取得
    return st.session_state.get("dev_role", "viewer")

    # フェーズ7（本番）: Googleログイン後はこちら
    # email = getattr(st.user, "email", None)
    # if not email:
    #     return "viewer"
    # return USER_ROLES.get(email, "viewer")
```

---

## 16. 将来のGoogleログイン方針

今回は実装しない。将来フェーズで以下の設計で実装予定。

```python
# modules/permissions.py (将来追加)

USER_ROLES = {
    "DAVI_EMAIL_HERE@gmail.com": "admin",
    "SARA_EMAIL_HERE@gmail.com": "admin",
    "LAGO_EMAIL_HERE@gmail.com": "product_researcher",
}

def get_current_role() -> str:
    email = getattr(st.user, "email", None)
    if not email:
        return "viewer"
    return USER_ROLES.get(email.lower(), "viewer")
```

- `st.user.email` はStreamlit の Google OAuth 連携で取得
- 未登録メールアドレスは自動的に `viewer` 扱い
- `USER_ROLES` は `.env` または `st.secrets` で管理（ソースコードにメアドを書かない）

---

## 17. 将来追加予定の役割

今回は実装しない。将来追加しやすい構造にしておく。

### market_researcher（仲間A）

想定作業:
- 競合URL入力
- 競合の強み・弱み入力
- レビュー分析入力
- 差別化ポイント入力

将来追加時は `PAGE_PERMISSIONS` と `ACTION_PERMISSIONS` に追記するだけで対応可能にする。

### creative_researcher（仲間B）

想定作業:
- 参考画像URL入力
- 参考動画URL入力
- 広告素材メモ入力
- 使いたい雰囲気入力
- NGな雰囲気入力

将来追加時は同様に `PAGE_PERMISSIONS` と `ACTION_PERMISSIONS` に追記するだけで対応可能にする。

---

## 18. ステータス一覧

| ステータス | 説明 | 次のアクション |
|-----------|------|--------------|
| `商品準備中` | Iagoが入力中 | Iagoが「準備完了」を押す |
| `Davi確認待ち` | 承認待ち（Daviが主担当） | Davi/Saraが承認または差し戻し |
| `Sara確認待ち` | 承認待ち（Saraが主担当） | Saraが承認または差し戻し |
| `差し戻し` | 修正依頼あり | Iagoが修正して再提出 |
| `承認済み` | 商品準備承認済み | Core生成が可能 |
| `Core生成可能` | 承認済み = Core生成可能 | Davi/SaraがCore生成 |
| `Core作成中` | Core生成処理中 | 完了待ち |
| `Core確認待ち` | Core生成完了・確認待ち | Davi/SaraがCore確認 |
| `Core承認済み` | Core承認完了 | Saraがページ・画像作成 |
| `ページ作成中` | Shopifyページ作成中 | Sara作業中 |
| `ページ確認待ち` | ページ確認待ち | Daviが確認 |
| `ページ完成` | ページ完成 | 画像・動画作業へ |
| `画像・動画作成中` | 画像プロンプト・動画台本作成中 | Sara作業中 |
| `SNS素材作成中` | SNS投稿文・広告コピー作成中 | Davi作業中 |
| `投稿準備完了` | 全素材完成・投稿待ち | Daviが最終確認 |
| `完了` | 全工程完了 | アーカイブ |

---

## 付録: 実装時の安全チェックリスト

実装を始める前に以下を確認すること:

```
[ ] data/ 全体のバックアップZIPが存在する
[ ] バックアップZIPをローカルに保管した
[ ] 変更前の app.py を app.py.bak_YYYYMMDD としてコピーした
[ ] git commit で現状コードを記録した
[ ] 変更するファイルを明確にリストアップした
[ ] 変更しないファイルのリストを確認した
[ ] 既存機能の動作確認リストを用意した
[ ] Phase単位で実装・確認することを約束した
```

実装完了の確認チェックリスト:

```
[ ] 既存の保存データが正常に読み込めるか
[ ] Core生成が正常に動くか
[ ] 保存・削除が正常に動くか
[ ] 承認フローが壊れていないか
[ ] バックアップ・ゴミ箱が動くか
[ ] i18n（日本語・Português）切り替えが動くか
[ ] 翻訳処理が壊れていないか
```

---

*以上が Task Destroyer チーム運用仕様書 v0.1 です。*  
*Davi の確認・承認後、Phase 2 から順番に実装を進めます。*
