# Task Destroyer チーム運用仕様書 v2.0

**バージョン**: 2.0  
**作成日**: 2026-05-04  
**ステータス**: Plan（レビュー待ち・未実装）  
**対象読者**: Davi / Sara / Iago

---

## 目次

1. [Task Destroyerの目的](#1-task-destroyerの目的)
2. [Davi / Sara / Iago の役割](#2-davi--sara--iago-の役割)
3. [各役割ができること](#3-各役割ができること)
4. [各役割が見れるページ](#4-各役割が見れるページ)
5. [各役割が押せるボタン](#5-各役割が押せるボタン)
6. [Core生成前の承認フロー](#6-core生成前の承認フロー)
7. [未承認ではCore生成できないルール](#7-未承認ではcore生成できないルール)
8. [未承認ではAPIを呼ばないルール](#8-未承認ではapiを呼ばないルール)
9. [Português入力から日本語確認への翻訳フロー](#9-português入力から日本語確認への翻訳フロー)
10. [UI言語と生成物言語を分けるルール](#10-ui言語と生成物言語を分けるルール)
11. [保存データ構造案](#11-保存データ構造案)
12. [APIクレジットを無駄に使わないルール](#12-apiクレジットを無駄に使わないルール)
13. [画像プロンプト・動画台本・広告SNS 選択式生成仕様](#13-画像プロンプト動画台本広告sns-選択式生成仕様)
14. [既存機能を壊さないために触ってはいけない部分](#14-既存機能を壊さないために触ってはいけない部分)
15. [安全な実装順序](#15-安全な実装順序)
16. [将来追加予定の役割](#16-将来追加予定の役割)
17. [ステータス一覧](#17-ステータス一覧)

---

## 1. Task Destroyerの目的

Task Destroyerは、Davi・Sara・Iagoの3人が **商品準備から投稿準備まで**を一貫して管理するためのチーム業務ツールです。

### 業務フロー全体像

```
Iago
  ↓ 商品情報をPortuguêsで入力・保存
  ↓ 商品準備完了ボタンを押す

Davi または Sara
  ↓ 内容をPortuguês原文またはJA翻訳で確認
  ↓ 問題なければ「商品準備承認」
  ↓ （問題あれば差し戻し → Iagoが修正）

Core生成が解禁される
  ↓
Davi または Sara
  ↓ Core生成・編集・承認

Sara
  ↓ Shopifyページ・画像プロンプト・動画台本作成

Davi
  ↓ SNS運用・広告コピー・最終確認
  ↓ 投稿準備完了
```

### 設計上の最重要原則

| 原則 | 内容 |
|------|------|
| データ安全 | 保存済みデータを絶対に削除・上書きしない |
| 原文保護 | IagoのPortuguês原文は上書きしない。翻訳は別フィールドに保存 |
| 生成物保護 | Core本文・Shopifyコード・台本・SNS文は自動翻訳しない |
| クレジット保護 | 承認前・権限なし・未選択では Anthropic API を呼ばない |
| 二重ガード | UIでのボタン非表示に加え、処理直前でも権限と承認状態を確認する |

---

## 2. Davi / Sara / Iago の役割

| 名前 | role | 担当領域 |
|------|------|---------|
| Davi | `admin` | 全権限。承認・SNS運用・最終確認が主な担当 |
| Sara | `admin` | 全権限。Shopifyページ・画像・動画制作が主な担当 |
| Iago | `product_researcher` | 商品情報の調査・入力のみ。生成・承認・削除は不可 |

### roleの定義

```python
# 開発フェーズ: サイドバーで仮切り替え
# 本番フェーズ: Googleログイン後のメールアドレスで判定

USER_ROLES = {
    "davi@example.com": "admin",
    "sara@example.com": "admin",
    "iago@example.com": "product_researcher",
    # 未登録メールアドレス → "viewer"（アプリ本体を表示しない）
}
```

---

## 3. 各役割ができること

### admin（Davi・Sara）

**商品管理**
- 全商品の閲覧・読み込み
- 商品情報の編集・保存
- 商品の削除（ゴミ箱方式）
- ゴミ箱からの復元
- バックアップ作成・リストア

**承認・差し戻し**
- 商品準備の承認
- 商品準備の差し戻し（コメント付き）
- Core承認
- 最終承認

**生成**
- Core生成（承認済み商品のみ）
- Core編集
- Shopifyコード生成
- 画像プロンプト生成
- 動画台本生成
- 広告・SNS文生成
- 一括生成

**翻訳・確認**
- Português原文の日本語翻訳（確認用）
- 翻訳結果の保存（原文は上書きしない）

**出力**
- ZIPエクスポート
- 作業指示書出力

---

### product_researcher（Iago）

**できること**
- 商品情報をPortuguêsで入力
  - 商品名
  - 商品URL
  - 価格
  - カテゴリ
  - ターゲット
  - 商品説明
  - 特徴
  - ブランドトーン
- 商品準備メモの入力
- 参考URLの入力
- 競合URLの入力
- 下書き保存
- 「商品準備完了」ボタンを押してDaviへ提出

**できないこと**
- Core生成・Core編集・Core承認
- 商品準備の承認・差し戻し
- Shopifyコード生成
- 画像プロンプト生成
- 動画台本生成
- 広告・SNS文生成
- 商品の削除
- バックアップ・リストア
- 最終承認
- 翻訳の実行

---

### viewer（未登録ユーザー）

- アプリ本体を表示しない
- 「このアカウントにはアクセス権限がありません。管理者に連絡してください。」のみ表示
- セッション変数に何も書き込まない

---

## 4. 各役割が見れるページ

### admin（全ページ表示可能）

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
✅ 保存データ管理（全タブ）
✅ エクスポートセンター
✅ 作業指示書
```

### product_researcher（Iago）

```
✅ ホームダッシュボード（自分が担当している商品のみ）
✅ 商品入力（商品準備フィールドのみ・Português表示）

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
❌ 保存データ管理（削除・バックアップ・復元不可）
❌ エクスポートセンター
❌ 作業指示書
```

### viewer

```
❌ 全ページ非表示
⚠️ アクセス権限なしメッセージのみ表示
```

---

## 5. 各役割が押せるボタン

### admin

| ボタン | 備考 |
|--------|------|
| 保存 | 全商品 |
| 読み込み | 全商品 |
| 削除（ゴミ箱へ移動） | 全商品 |
| ゴミ箱から復元 | — |
| 永久削除 | 確認ダイアログ必須 |
| 商品準備承認 | — |
| 商品準備差し戻し | — |
| 日本語に変換（翻訳） | 確認用のみ・原文上書きなし |
| Core生成 | 要: 商品準備承認済み |
| Core編集・保存 | — |
| Core承認 | — |
| Shopifyコード生成 | — |
| 画像プロンプト生成（選択式） | — |
| 動画台本生成（選択式） | — |
| 広告・SNS生成（選択式） | — |
| 一括生成 | — |
| 全保存データをバックアップ | — |
| バックアップから復元 | 自動事前バックアップあり |
| ZIPエクスポート | — |
| 最終承認 | — |

### product_researcher（Iago）

| ボタン | 備考 |
|--------|------|
| 保存（下書き） | 自分の担当商品のみ |
| 商品準備完了（提出） | ステータスを「Davi確認待ち」に変更 |

**押せないボタン（表示しないまたは disabled）**

| ボタン | 理由 |
|--------|------|
| Core生成 | product_researcherには不可 |
| 承認 | product_researcherには不可 |
| 差し戻し | product_researcherには不可 |
| 削除 | product_researcherには不可 |
| 翻訳 | product_researcherには不可 |
| Shopify/画像/動画/SNS生成 | product_researcherには不可 |
| バックアップ | product_researcherには不可 |

---

## 6. Core生成前の承認フロー

```
Step 1
  Iago が商品情報を Português で入力
  → created_by: "iago"
  → input_original_language: "pt"
  → current_status: "商品準備中"
  → product_prep_approved: false

Step 2
  Iago が「商品準備完了」ボタンを押す
  → current_status: "Davi確認待ち"

Step 3
  Davi または Sara が商品内容を確認
  → 必要なら「日本語に変換」ボタンで input_ja を生成
  → input_original は上書きしない

Step 4a【承認の場合】
  Davi または Sara が「商品準備承認」ボタンを押す
  → product_prep_approved: true
  → product_prep_approved_by: "davi" または "sara"
  → product_prep_approved_at: タイムスタンプ
  → current_status: "承認済み / Core生成可能"
  → Core生成ボタンが有効になる

Step 4b【差し戻しの場合】
  Davi または Sara が「差し戻し」ボタンを押す
  → current_status: "差し戻し"
  → product_prep_approval_note: 差し戻しコメント（Português翻訳対象）
  → Iago が修正 → Step 2 へ戻る

Step 5
  Davi または Sara が Core 生成
  → 条件を満たさない場合はAPIを絶対に呼ばない（後述）
  → current_status: "Core作成中" → "Core確認待ち"

Step 6
  Sara が Shopify ページ・画像・動画作成
  → current_status: "ページ作成中" → "画像・動画作成中"

Step 7
  Davi が SNS 運用・最終確認
  → current_status: "SNS素材作成中" → "投稿準備完了" → "完了"
```

---

## 7. 未承認ではCore生成できないルール

### ゲートの二重構造

**UIレベル（第1の壁）**

```
Core生成ボタンの状態:
  product_prep_approved == false  →  disabled（押せない）
  role != "admin"                 →  disabled（押せない）
  上記に該当する場合:
    「管理者の承認が完了するまでCore生成はできません」と表示
```

**処理レベル（第2の壁・必須）**

```python
# Core生成処理を実行する直前に必ずチェック
def _guard_core_generation(role: str, project: dict):
    if role != "admin":
        st.error("Core生成には管理者権限が必要です。")
        st.stop()
    if not project.get("product_prep_approved", False):
        st.error("管理者の承認が完了するまでCore生成はできません。")
        st.stop()
    if not project.get("name", "").strip():
        st.error("商品名が入力されていません。")
        st.stop()
```

**重要**: UIでボタンを隠すだけでは不十分。セッション操作やバグで通り抜けるリスクがあるため、**処理実行直前にも必ず roleと承認状態を確認する**。

---

## 8. 未承認ではAPIを呼ばないルール

### API呼び出しが許可される条件

| 条件 | 必須 |
|------|------|
| role == "admin" | ✅ |
| product_prep_approved == true | ✅（Core生成のみ） |
| core_textが空でない | ✅（Core以外の生成） |
| 生成する項目が1つ以上選択されている | ✅（選択式生成） |
| 商品名が入力されている | ✅ |

### APIエラー文を保存しないルール

以下のパターンがAPIレスポンスに含まれていた場合、**保存データに書き込まない**：

```python
_API_ERROR_PATTERNS = [
    "Your credit balance is too low",
    "Anthropic APIエラー",
    "invalid_request_error",
    "Error code: 400",
    "Error code: 529",
    "overloaded_error",
]

def _is_api_error(text: str) -> bool:
    return any(p in text for p in _API_ERROR_PATTERNS)

# 生成後・保存前に必ずチェック
if _is_api_error(result):
    st.error("APIエラーが発生しました。この内容は保存しません。")
    return  # save_generated() を呼ばない
```

### クレジット不足時の対応

```
"Your credit balance is too low" を受信した場合:
  → 「APIクレジットが不足しています。Anthropicダッシュボードで残高を確認してください。」と表示
  → 生成結果として保存しない
  → 既存の保存データは上書きしない
```

---

## 9. Português入力から日本語確認への翻訳フロー

### 基本方針

```
Iago が Português で入力・保存
  → input_original に原文を保存
  → input_original は絶対に上書きしない

Davi または Sara が確認したい時だけ
  → 「日本語に変換」ボタンを押す（admin専用）
  → input_ja に翻訳結果を保存
  → 原文(input_original)はそのまま維持

UI言語を切り替えただけでは翻訳しない
保存ボタンを押しただけでは翻訳しない
```

### 翻訳対象フィールド

以下は「日本語に変換」ボタンで翻訳してよいフィールド：

| フィールド | 翻訳可 |
|-----------|--------|
| 商品名（name） | ✅ |
| 商品説明（description） | ✅ |
| 商品準備メモ（memo） | ✅ |
| 競合分析メモ | ✅ |
| レビュー分析メモ | ✅ |
| 差別化ポイント | ✅ |
| 参考素材メモ | ✅ |
| 広告素材メモ | ✅ |
| 差し戻しコメント | ✅ |

### 翻訳してはいけないもの

以下は「日本語に変換」の対象外・UI言語を変えても翻訳しない：

| コンテンツ | 理由 |
|-----------|------|
| Core本文 | 確定済みブランド戦略テキスト |
| Shopifyコード（HTML/CSS/JS） | コードを壊す可能性がある |
| 画像プロンプト | AI生成指示文 |
| 動画台本 | 確定済み台本 |
| 広告・SNS文 | 確定済み投稿文 |
| 承認済みコンテンツ全般 | 変更不可 |
| 保存済み生成物全般 | 変更不可 |

### 翻訳データの保存構造

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

## 10. UI言語と生成物言語を分けるルール

### UI言語（切り替えてよいもの）

```
メニュー名
ボタンラベル
入力フォームのラベル・プレースホルダー
説明文・ヘルプテキスト
ステータス表示
エラーメッセージ
タブ名
承認フローのラベル
サイドバーのナビゲーション
```

→ `i18n/ja.json` と `i18n/pt.json` で管理。  
→ `st.session_state.lang` で切り替え。  
→ Iago の画面は Português 表示を基本とする。

### 生成物言語（UI言語を切り替えても変えてはいけないもの）

```
Core本文
商品ページ本文
Shopifyコード（HTML/CSS/JavaScript）
画像プロンプト
動画台本
広告・SNS文
保存済み生成物全般
```

→ ファイルに保存された内容をそのまま表示する。  
→ UI言語の変更は表示ラベルのみに影響し、保存データの内容には一切影響しない。

### 実装上の禁止事項

```python
# ❌ 禁止: 生成物にt()（翻訳関数）を通す
st.text_area(value=t(st.session_state.core_text))  # NG

# ❌ 禁止: lang変更時に生成物を自動翻訳
if lang_changed:
    st.session_state.core_text = translate(st.session_state.core_text)  # NG

# ✅ 正しい: UIラベルだけi18nを使う
st.text_area(label=t("core.label"), value=st.session_state.core_text)  # OK
```

---

## 11. 保存データ構造案

### 現在の保存場所（変更しない）

| フォルダ | 内容 | 重要度 |
|---------|------|--------|
| `data/projects/` | 商品メタデータ + 生成コンテンツファイル | ★★★ |
| `data/core_library/` | Coreテキスト全バージョン | ★★★ |
| `data/approvals/` | 承認状態 | ★★★ |
| `data/activity_logs/` | 操作ログ（JSONL） | ★★ |
| `data/delete_logs/` | 削除記録 | ★★ |
| `data/trash/` | ソフト削除済みデータ | ★★ |
| `data/backups/` | ZIPバックアップ | ★★ |

### ファイル命名規則（変更しない）

```
data/projects/
  {pid}.json                         ← 商品メタデータ本体
  {pid}_{content_type}_{id}.json     ← 生成コンテンツ（同フォルダ内に混在）

data/core_library/
  {pid}_{core_id[:8]}.json           ← Coreバージョン

data/approvals/
  {pid}_{content_type}.json          ← 承認状態
```

### 権限管理追加後の拡張フィールド

`data/projects/{pid}.json` に追加予定のフィールド（古いデータにないキーはデフォルト値で補完する）：

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

  // ─── 権限管理フェーズで追加 ───────────────────────────────────
  "created_by": "iago",
  "current_status": "商品準備中",

  // ─── 翻訳フェーズで追加 ──────────────────────────────────────
  "input_original_language": "pt",
  "input_original": {},
  "input_ja": {},
  "translation_status": "not_translated",
  "translated_at": "",
  "translated_by": "",

  // ─── 承認フローフェーズで追加 ────────────────────────────────
  "product_prep_approved": false,
  "product_prep_approved_by": "",
  "product_prep_approved_at": "",
  "product_prep_approval_note": "",

  "core_approved": false,
  "core_approved_by": "",
  "core_approved_at": "",

  // ─── 監査ログ ─────────────────────────────────────────────────
  "workflow_logs": [],
  "permissions_version": 1
}
```

### 古いデータでも落ちないようにするルール

```python
# storage.py または app.py の load_product() 呼び出し後に適用
_PERMISSION_DEFAULTS = {
    "created_by": "",
    "current_status": "商品準備中",
    "input_original_language": "ja",
    "input_original": {},
    "input_ja": {},
    "translation_status": "not_translated",
    "translated_at": "",
    "translated_by": "",
    "product_prep_approved": False,
    "product_prep_approved_by": "",
    "product_prep_approved_at": "",
    "product_prep_approval_note": "",
    "core_approved": False,
    "core_approved_by": "",
    "core_approved_at": "",
    "workflow_logs": [],
    "permissions_version": 0,
}

def _fill_defaults(data: dict) -> dict:
    for key, default in _PERMISSION_DEFAULTS.items():
        if key not in data:
            data[key] = default
    return data
```

---

## 12. APIクレジットを無駄に使わないルール

### ガードすべきケースと対応

| ケース | 対応 |
|--------|------|
| role が admin でない | APIを呼ばない・エラー表示 |
| product_prep_approved が false | APIを呼ばない・メッセージ表示 |
| core_text が空 | APIを呼ばない・メッセージ表示 |
| 選択式生成でチェックが0件 | APIを呼ばない・「項目を選択してください」と表示 |
| 商品名が空 | APIを呼ばない・メッセージ表示 |
| APIエラー文が返ってきた | 保存しない・エラー表示のみ |
| クレジット残高不足 | 保存しない・「残高を確認してください」と表示 |

### 選択式生成でのクレジット節約

```
チェックされた項目のみ API を呼ぶ
  → 10項目あっても3項目だけチェックなら API は3回のみ

チェックされていない項目:
  → 生成しない
  → APIを呼ばない
  → 既存の保存データを上書きしない
  → ダウンロードボタンも出さない
```

### 再生成のルール

```
「再生成」ボタンは1項目ずつ存在する
  → 押された項目だけAPIを1回呼ぶ
  → 他の項目は変更しない
  → 保存済みの他の項目を上書きしない
```

---

## 13. 画像プロンプト・動画台本・広告SNS 選択式生成仕様

### 共通ルール

- カテゴリ（画像/動画/SNS）ごとに生成する項目をチェックボックスで選択
- チェックされた項目のみ API を呼ぶ
- 生成結果は1項目ずつカード表示
- 各カードに以下を表示：
  - 承認ステータスバッジ
  - 生成テキスト（編集可能）
  - 保存ボタン
  - 再生成ボタン（その項目のみ再生成）
  - ダウンロードボタン

### 画像プロンプト（8項目）

| キー | 表示名 |
|------|--------|
| `main_visual` | 商品ページ メインビジュアル |
| `product_only` | 商品単体画像 |
| `usage_scene` | 使用シーン画像 |
| `benefit` | ベネフィット訴求画像 |
| `comparison` | 比較画像 |
| `ad_banner` | 広告バナー |
| `sns_post` | SNS投稿用画像 |
| `story` | ストーリー用画像 |

**プリセット**

| プリセット名 | 選択される項目 |
|------------|--------------|
| Shopifyページ制作セット | main_visual, product_only, usage_scene, benefit |
| SNS素材セット | sns_post, story, ad_banner |
| 広告運用セット | ad_banner, comparison, benefit |
| フル生成 | 全8項目 |
| カスタム | 手動で選択 |

### 動画台本（11項目）

| キー | 表示名 |
|------|--------|
| `script_15s` | 15秒動画台本 |
| `script_30s` | 30秒動画台本 |
| `script_45s` | 45秒動画台本 |
| `script_60s` | 60秒動画台本 |
| `tiktok` | TikTok用台本 |
| `reels` | Reels用台本 |
| `yt_shorts` | YouTube Shorts用台本 |
| `narration` | ナレーション原稿 |
| `timeline` | 撮影タイムライン |
| `telop` | テロップ原稿 |
| `shooting` | 撮影指示書 |

**プリセット**

| プリセット名 | 選択される項目 |
|------------|--------------|
| SNS投稿セット | script_15s, tiktok, reels, yt_shorts |
| 広告運用セット | script_30s, script_60s, narration, telop |
| フル生成 | 全11項目 |
| カスタム | 手動で選択 |

### 広告・SNS（8媒体 × 7コンテンツ種別 = 最大56項目）

**媒体（8種）**

| キー | 表示名 |
|------|--------|
| `instagram` | Instagram |
| `tiktok` | TikTok |
| `yt_shorts` | YouTube Shorts |
| `facebook` | Facebook |
| `x` | X（旧Twitter） |
| `line` | LINE |
| `shopify_ad` | Shopify広告 |
| `google_ad` | Google広告 |

**コンテンツ種別（7種）**

| キー | 表示名 |
|------|--------|
| `post` | 投稿文 |
| `ad_copy` | 広告コピー |
| `caption` | キャプション |
| `hashtag` | ハッシュタグ |
| `cta` | CTA文 |
| `hook` | フック文 |
| `comment_bait` | コメント誘導文 |

**アイテムキー形式**: `"{media}::{content_type}"`（例: `"instagram::post"`）

**プリセット**

| プリセット名 | 選択される組み合わせ |
|------------|------------------|
| SNS投稿セット | instagram::post, tiktok::post, yt_shorts::post, x::post |
| 広告運用セット | instagram::ad_copy, facebook::ad_copy, google_ad::ad_copy, shopify_ad::ad_copy |
| カスタム | 手動で選択 |

---

## 14. 既存機能を壊さないために触ってはいけない部分

### ★★★ 絶対に変えてはいけない処理

| 処理 | 場所 | 変えると起きること |
|------|------|------------------|
| `list_products()` の除外ロジック | `storage.py` | 既存データが一覧に出なくなる |
| `save_generated()` のファイル命名規則 | `storage.py` | 既存の生成データが読めなくなる |
| `delete_project(use_trash=True)` のデフォルト | `storage.py` | ゴミ箱に行かず完全削除になる |
| `_load_project_session()` の基本構造 | `app.py` | セッション全体が壊れる |
| Core生成・Shopify生成のAPIプロンプト | `generator_engine.py` | 生成品質が変わる |
| 翻訳ロジック | `translator.py` | 既存翻訳が壊れる |
| API接続 | `llm_client.py` | 全生成機能が止まる |

### ★★ 変更に注意が必要な処理

| 処理 | 注意点 |
|------|--------|
| `save_product()` | フィールドをマージする（置き換えない） |
| `load_product()` でのデフォルト補完 | 既存フィールドを削除しない |
| サイドバーのページ遷移ロジック | 変えると全ページにアクセス不可になる |
| `init_state()` | セッション初期化は慎重に追記のみ |
| `get_services()` の`@st.cache_resource` | キャッシュを外すとパフォーマンスが落ちる |
| i18n の既存キー | 削除・変更するとUI文字が壊れる |

### ★ 新規追加のみ許容する処理

| 処理 | 対応方針 |
|------|---------|
| 保存データ構造 | 新フィールドを**追加のみ**（既存フィールドは削除しない） |
| `page_product_input()` の入力フォーム | 新フィールドを下に**追加のみ** |
| `page_approval()` の承認UI | 既存承認ロジックを壊さず**追記のみ** |

---

## 15. 安全な実装順序

### Phase 0：実装前の準備（必須）

```
[ ] data/ 全体のバックアップZIPを作成してローカルPCに保存
[ ] バックアップZIPに .env や secrets.toml が含まれていないことを確認
[ ] git commit で現状コードを記録
[ ] app.py を app.py.bak_YYYYMMDD としてコピー
[ ] どのファイルを触るかリストアップして合意を取る
```

### Phase 1：仕様書の確認（今回）

```
[ ] 本仕様書のレビュー・修正
[ ] ページ許可リスト最終確認
[ ] 操作許可リスト最終確認
[ ] DaviのOK → Phase 2 に進む
```

### Phase 2：開発用 role 仮切り替え

**触るファイル**: `app.py`（サイドバー追加）、`modules/permissions.py`（新規作成）

```python
# サイドバーに追加
dev_role_options = {
    "Davi (admin)": ("davi", "admin"),
    "Sara (admin)": ("sara", "admin"),
    "Iago (product_researcher)": ("iago", "product_researcher"),
    "viewer": ("", "viewer"),
}
selected = st.selectbox("役割切り替え", list(dev_role_options.keys()))
st.session_state.dev_user, st.session_state.dev_role = dev_role_options[selected]
```

```python
# modules/permissions.py（新規作成）
def get_current_role() -> str:
    return st.session_state.get("dev_role", "viewer")

def can_view_page(role: str, page_name: str) -> bool: ...
def can_perform_action(role: str, action_name: str) -> bool: ...
def require_permission(role: str, action_name: str): ...
```

**確認ポイント**
- Iago role で Core生成ページが非表示になるか
- admin role で全ページが表示されるか
- viewer で「アクセス権限なし」が表示されるか
- 既存の保存・生成・削除が壊れていないか

### Phase 3：承認ゲート

**触るファイル**: `modules/storage.py`（デフォルト補完追加）、`app.py`（承認UI追加・Core生成ゲート追加）

```
[ ] _fill_defaults() を storage.py に追加
[ ] load_product() の返値に _fill_defaults() を適用
[ ] Core生成ボタンに can_generate_core() チェックを追加
[ ] Core生成処理直前に require_permission() を追加
[ ] 「商品準備承認」「差し戻し」ボタンを admin 専用で追加
[ ] 承認状態バッジを表示
```

**確認ポイント**
- 未承認では Core 生成ボタンが disabled になるか
- 承認後に Core 生成ボタンが有効になるか
- 既存の Core 生成ロジックが壊れていないか
- 既存の保存データが正常に読み込めるか

### Phase 4：Português入力と日本語確認

**触るファイル**: `app.py`（商品入力UI調整、翻訳ボタン追加）、`modules/storage.py`（翻訳フィールド保存）、`i18n/pt.json`（Iago向けラベル追記）

```
[ ] input_original / input_ja フィールドの保存・読み込み
[ ] Iago role で Português ラベルに切り替わるか確認
[ ] 「日本語に変換」ボタン（admin専用）を追加
[ ] 翻訳結果を input_ja に保存
[ ] input_original が上書きされていないことを確認
[ ] 古いデータに翻訳フィールドがなくても落ちないことを確認
```

### Phase 5：選択式生成（確認・権限チェック追加）

既存の選択式生成UIは実装済み。  
権限チェック（adminのみ生成可）とAPIエラーガードを追加する。

```
[ ] 生成ボタンに require_permission("admin") を追加
[ ] APIエラー文を検知して保存しない処理を追加
[ ] 選択ゼロでは生成ボタンをdisabledにする
```

### Phase 6：保存データ保護（確認）

バックアップ・ゴミ箱・復元は実装済み。  
動作確認のみ。

### Phase 7：Googleログイン（将来・今回対象外）

```python
# 将来実装予定
USER_ROLES = {
    "davi@gmail.com": "admin",
    "sara@gmail.com": "admin",
    "iago@gmail.com": "product_researcher",
}

def get_current_role() -> str:
    email = getattr(st.user, "email", None)
    if not email:
        return "viewer"
    return USER_ROLES.get(email.lower(), "viewer")
```

---

## 16. 将来追加予定の役割

今回は実装しない。将来 `PAGE_PERMISSIONS` と `ACTION_PERMISSIONS` に追記するだけで対応できる構造にしておく。

### market_researcher（仲間A）

想定作業：競合URL・強み・弱み・レビュー分析・差別化ポイントの入力

### creative_researcher（仲間B）

想定作業：参考画像URL・参考動画URL・広告素材メモ・使いたい雰囲気・NGな雰囲気の入力

---

## 17. ステータス一覧

| ステータス | 次のアクション | 担当 |
|-----------|--------------|------|
| `商品準備中` | 「商品準備完了」ボタンを押す | Iago |
| `Davi確認待ち` | 内容確認・承認または差し戻し | Davi |
| `Sara確認待ち` | 内容確認・承認または差し戻し | Sara |
| `差し戻し` | 修正して再提出 | Iago |
| `承認済み / Core生成可能` | Core生成 | Davi または Sara |
| `Core作成中` | 完了待ち | — |
| `Core確認待ち` | Core確認・承認 | Davi または Sara |
| `Core承認済み` | Shopifyページ・画像・動画作成 | Sara |
| `ページ作成中` | 作業中 | Sara |
| `ページ確認待ち` | ページ確認 | Davi |
| `ページ完成` | 画像・動画作業へ | Sara |
| `画像・動画作成中` | 作業中 | Sara |
| `SNS素材作成中` | 作業中 | Davi |
| `投稿準備完了` | 最終確認 | Davi |
| `完了` | アーカイブ | — |

---

## 付録A：権限チェック関数の設計案

```python
# modules/permissions.py（新規作成予定）

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

def get_current_role() -> str:
    # Phase 2（開発用）
    return st.session_state.get("dev_role", "viewer")

def can_view_page(role: str, page_name: str) -> bool:
    allowed = PAGE_PERMISSIONS.get(role, [])
    return allowed == "__all__" or page_name in allowed

def can_perform_action(role: str, action_name: str) -> bool:
    allowed = ACTION_PERMISSIONS.get(role, [])
    return allowed == "__all__" or action_name in allowed

def can_generate_core(role: str, project: dict) -> bool:
    return role == "admin" and project.get("product_prep_approved", False)

def can_delete_project(role: str) -> bool:
    return role == "admin"

def require_permission(role: str, action_name: str):
    if not can_perform_action(role, action_name):
        st.error("この操作を行う権限がありません。")
        st.stop()
```

---

## 付録B：実装前チェックリスト

実装フェーズを始める前に必ず確認：

```
[ ] data/projects/ に既存データがあるか確認
[ ] data/ 全体のバックアップZIPを作成・保存
[ ] バックアップにAPIキーや .env が含まれていないことを確認
[ ] git commit（変更前の状態を記録）
[ ] 変更するファイルを明確にリストアップした
[ ] 変更しないファイルのリストを確認した
[ ] Daviから「このPhaseをOK」をもらった
```

実装完了の確認：

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

*Task Destroyer チーム運用仕様書 v2.0*  
*Daviのレビュー・承認後、Phase 2から順に実装を進めます。*
