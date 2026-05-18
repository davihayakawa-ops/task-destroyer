import re
from typing import Optional
from .llm_client import LLMClient

PRODUCT_PAGE_PROMPT = """
あなたはShopify商品ページ制作の専門家です。
以下のCoreをベースに、指定された販売先市場向けの商品ページコンテンツを生成してください。

【Core】
{core}

【商品情報】
{product_info}

【生成する商品ページコンテンツ】

## 商品タイトル（3案）

## キャッチコピー（5案）

## ファーストビュー文言（3案）

## 商品説明文（標準版）

## 商品説明文（短め版）

## 商品説明文（上品バージョン）

## LP構成案

## セクション見出し

## ベネフィット一覧

## 使用シーン

## おすすめ対象

## 使用方法

## FAQ（5個）

## 注意事項

## SEOタイトル

## SEOディスクリプション

## 商品タグ（10個）

## SNS向け短文説明

重要：
- 指定された出力言語で、販売先市場に合う自然で信頼感のある表現を使うこと
- 断定表現・医療的表現・根拠のない保証表現は避けること
- Coreの訴求軸と一貫した内容にすること
"""

IMAGE_PROMPT_PROMPT = """
あなたは画像生成AIのプロンプト作成の専門家です。
以下のCoreをベースに、Shopify商品ページと広告用の画像生成プロンプトを作成してください。

【Core】
{core}

【商品情報】
商品名: {product_name}
カテゴリ: {category}

【生成する画像プロンプト】

## 商品メイン画像
目的：
構図：
背景：
光：
色味：
雰囲気：
商品の見せ方：
NG要素：
生成AIに貼り付けるプロンプト（英語）：

## LPファーストビュー画像
（同様の形式）

## 使用シーン画像
（同様の形式）

## 高級感訴求画像
（同様の形式）

## 悩み訴求画像
（同様の形式）

## Instagram投稿画像
（同様の形式）

## 広告バナー
（同様の形式）

各プロンプトの生成AIに貼り付けるプロンプトは英語で、具体的で詳細に書くこと。
販売先市場の美的感覚（清潔感、信頼感、ブランド感）を反映すること。
"""

VIDEO_SCRIPT_PROMPT = """
あなたは動画台本の専門家です。
以下のCoreをベースに、TikTok・Instagram Reels・YouTube Shorts向けの動画台本を作成してください。

【Core】
{core}

【商品情報】
商品名: {product_name}

【生成する動画台本】

## 15秒動画台本（TikTok/Reels向け）

構成：
0〜3秒：フック
4〜8秒：悩み提示
9〜12秒：商品紹介・ベネフィット
13〜15秒：CTA

ナレーション：
テロップ案：
映像指示：
フック文言（3案）：
BGM方向性：

## 30秒動画台本

構成：
0〜3秒：フック
4〜10秒：悩み提示
11〜20秒：商品紹介・ベネフィット
21〜27秒：安心材料
28〜30秒：CTA

ナレーション：
テロップ案：
映像指示：

## 60秒動画台本（YouTube Shorts向け）

構成：
0〜5秒：フック
6〜15秒：悩み提示・共感
16〜35秒：商品紹介・ベネフィット詳細
36〜50秒：安心材料・FAQ
51〜60秒：CTA

ナレーション：
テロップ案：
映像指示：

## UGC風動画台本

## 上品ブランド風動画台本

## 広告用動画台本

重要：
- 最初の3秒のフックを特に強くすること
- 指定された出力言語で自然で柔らかい表現にすること
- 購買意欲を高めつつ押しつけがましくならないようにすること
"""

CUSTOM_LIQUID_PROMPT = """
あなたはShopifyのカスタムLiquidコード制作の専門家です。
以下のCoreと商品情報をもとに、ShopifyのテーマエディターにあるCustom Liquidブロックにそのまま貼り付けて使える、完成したHTMLとCSSのコードを生成してください。

【Core】
{core}

【商品情報】
商品名: {product_name}
カテゴリ: {category}
価格: {price}
商品説明: {description}
特徴・強み: {features}
ターゲット: {target}
使用シーン: {use_scenes}

【生成ルール】
- <html> <head> <body> タグは不要（Custom Liquidブロックに直接貼るため）
- JavaScriptは使わない
- 外部CSS・外部ライブラリは使わない
- CSSは <style> タグ内にすべてまとめる
- Shopifyの他テーマに影響しないよう、全CSSクラス名には必ず「td-」プレフィックスを付ける
- スマホ・PC両対応のレスポンシブデザインにする（max-width: 768px でメディアクエリを入れる）
- 上品で読みやすい、商品ページに合うデザインにする
- 薬機法・景表法リスクのある表現（「治る」「必ず」「確実に」「医学的に証明」等）は絶対に使わない
- 指定された出力言語で自然で丁寧な表現にする

【含めるセクション】
1. キャッチコピー（大きな見出し）
2. 商品説明文（読みやすいテキスト）
3. ベネフィット（アイコン的なカードで3〜5個）
4. こんな方におすすめ（箇条書きまたはカード）
5. 使用シーン（テキストで2〜3個）
6. 商品の特徴（カードまたはリスト）
7. FAQ（<details><summary>タグを使ったアコーディオン形式、5個）
8. 注意事項（小さいテキスト）
9. CTAエリア（購入を促す一言 ＋ 区切り線）

【デザイン方針】
{design_instructions}

【販売先・出力言語】
{market_instructions}

【出力形式】
コードのみを出力してください。説明文・コメント・マークダウン記法（```）は不要です。
<style> から始まり、最後の </section> または </div> で終わる完結したコードとして出力してください。
"""

SNS_PROMPT = """
あなたはSNSマーケティングの専門家です。
以下のCoreをベースに、各SNS向けのコンテンツを生成してください。

【Core】
{core}

【商品情報】
商品名: {product_name}

【生成するSNSコンテンツ】

## Instagram広告文（3案）

## Instagram投稿キャプション（3案）

## TikTok広告文（3案）

## TikTok動画説明文

## Facebook広告文（3案）

## ハッシュタグ案（Instagram用・30個）

## ハッシュタグ案（TikTok用・20個）

## SNS投稿フック案（20個）

## CTA案（20個）

## 悩み訴求コピー（5案）

## 憧れ訴求コピー（5案）

## LINE配信用短文（3案）

重要：
- 各SNSのトーンと文化に合わせること
- 指定された出力言語で自然で親しみやすくすること
- 絵文字は適度に使うこと
- 商品の魅力を短く伝えること
"""


_SHOPIFY_RULES = """【共通ルール】
- <html><head><body>タグ不要 / JavaScriptなし / 外部CSS・ライブラリなし
- 全CSSクラス名は必ず「td-」プレフィックス
- @media(max-width:767px) でスマホ対応
- 日本市場では薬機法・景表法、米国市場ではFTC/FDA/広告審査で問題になりやすい表現を避ける
- 「治る」「必ず」「確実に」「医学的に証明」「guaranteed」「cure」「clinically proven」等の根拠なき断定表現は禁止
- コードのみ出力。マークダウン(```)や説明文は不要
【フォント】大見出し:clamp(28px,4vw,48px) / セクション見出し:clamp(24px,3vw,36px) / 小見出し:clamp(18px,2vw,24px) / 本文:clamp(16px,1.4vw,18px);line-height:1.8
【レイアウト】max-width:1100px;margin:0 auto;padding:80px 24px → スマホ:padding:48px 16px
【デザイン】{design_instructions}
【販売先・出力言語】{market_instructions}
01〜08は必ず .td-section と .td-container を使い、色は var(--td-bg) / var(--td-text) / var(--td-accent) / var(--td-card) / var(--td-border) を優先する。
CSS変数には必ずフォールバック値を入れる（例: var(--td-accent,#3d6b4f)）。"""

_SECTION_BASE_PROMPT = """あなたはShopifyのカスタムLiquid制作の専門家です。
1つのセクションのHTMLコードを生成してください。

【絶対ルール】
- 文章はすべて【Core】と【商品情報】の内容に基づいて書くこと
- 「〇〇」「（ここにテキスト）」などのプレースホルダーは使わない
- 商品名・ターゲット・訴求軸を文章に具体的に織り込む
- 汎用的なダミー文や一般論は書かない
{rules}
【Core】
{core}

【商品情報】
商品名:{product_name} / カテゴリ:{category} / 価格:{price}
説明:{description}
特徴:{features} / ターゲット:{target} / 使用シーン:{use_scenes}

【販売先・出力言語】
{market_context}

マーカーで囲んで出力してください：

<<<{marker}>>>
{instructions}
<<<END_SECTION>>>"""

SHOPIFY_SECTION_CONFIGS = [
    (
        "shopify_common_css",
        "SECTION_00_COMMON_CSS",
        "指定されたデザインオプションの色を正確に使った共通CSS。"
        ":root と .td-product-page にCSS変数（--td-bg / --td-text / --td-accent / --td-card / --td-border / --td-radius）を定義し、"
        ".td-section / .td-container / .td-badge / .td-card / .td-btn の基本クラスを定義。"
        "<style>タグのみ。<section>タグは含めない。固定の緑色など、指定外の色は使わない。",
    ),
    (
        "shopify_hero_section_code",
        "SECTION_01_HERO",
        """ファーストビュー（短め・印象的に）。<style>＋<section class="td-section td-hero">。

構成：
1. カテゴリバッジ：【商品情報】のカテゴリ名
2. H1キャッチコピー：【Core】のmain_appeal または concept を元にした15〜25字のインパクトある一言
   ※商品名をそのままH1にするのではなく、訴求コピーを書く
3. サブコピー：【Core】のconceptまたはunique_valueを使った2文（40〜60字）
4. ベネフィット3点：【Core】のbenefitsから3つ選びチェックマーク付きカードで表示
5. 信頼テキスト：【Core】のreassuranceから1〜2点を小さく表示（例：「累計〇〇件」等は使わず、定性的な安心感）

CSSはtd-hero内にスコープし、色はCSS変数を優先する。画面幅いっぱいの高さ固定・position:absolute・重なりやすい装飾は使わない。
文章はすべて指定された出力言語で、【Core】のbrand_toneに合わせて自然に書くこと。""",
    ),
    (
        "shopify_about_section_code",
        "SECTION_02_ABOUT",
        """商品について（やや詳しく）。<style>＋<section>。

構成：
1. セクション見出し：【商品情報】の商品名を使った「〜とは」形式の見出し
2. リード文：【Core】のconceptを元に2〜3文（60〜100字）。商品が生まれた背景・想いを含める
3. 「こんな方に」：【Core】のmain_target・sub_targetを元に2〜3タイプのカード
   各カード：絵文字＋ターゲット像の見出し（例：「忙しい毎日を送る方」）＋説明2文
4. 「こんな場面で」：【商品情報】のuse_scenesを元に2〜3シーン（アイコン＋シーン名＋説明1文）

すべての文章を【Core】のターゲット像・訴求軸に合わせて書くこと。""",
    ),
    (
        "shopify_problem_section_code",
        "SECTION_03_PROBLEM",
        """悩み・共感セクション（ターゲットに刺さる内容）。<style>＋<section>。

構成：
1. 見出し：「こんなお悩みはありませんか？」
2. 悩みリスト：【Core】のcustomer_painを元に4〜5項目
   各項目：😔 絵文字＋ターゲットの言葉で書いた具体的な悩み（20〜35字）
   ※一般論でなく【Core】のターゲット層が実際に感じる言葉で書く
3. 共感文：「そのお気持ち、よくわかります。」系の共感リード文1〜2文（40〜60字）
4. 解決提示ボックス（アクセントカラー背景）：
   - 見出し：【商品情報】の商品名を使った「〜が、その解決策になるかもしれません。」形式
   - 本文：【Core】のunique_valueとmain_appealを元に2〜3文（60〜100字）
   - 効果を断定せず「〜かもしれません」「〜のサポートができます」等の表現を使う

文章は【Core】のターゲット像・customer_painに忠実に書くこと。""",
    ),
    (
        "shopify_features_section_code",
        "SECTION_04_FEATURES",
        """特徴カードセクション（3〜6個）。CSS Grid 3列→スマホ1列。<style>＋<section>。

構成：
1. 見出し：「【商品情報】の商品名の特徴」
2. 特徴カード：【商品情報】のfeaturesと【Core】のUSP・unique_valueを元に3〜6個生成
   各カード：大きな絵文字（2rem）＋太字見出し（10字以内）＋説明文2〜3文（50〜80字）
   説明文は抽象的でなく具体的に。「〜できます」「〜設計になっています」など
3. カード数は【商品情報】のfeaturesに記載された強みの数に合わせる（最少3・最多6）

各カードの内容は【商品情報】の特徴欄の実際の強みを1カードで1項目ずつ表現すること。""",
    ),
    (
        "shopify_usage_scene_section_code",
        "SECTION_05_SCENES",
        """使用シーンセクション（3〜4シーン）。2列グリッド→スマホ1列。<style>＋<section>。

構成：
1. 見出し：「こんな場面で」「〜を使うシーン」など
2. シーンカード3〜4個：【商品情報】のuse_scenesを元に設定
   各カード：
   - 絵文字アイコン（2rem）
   - シーン見出し（例：「夜のリラックスタイムに」「忙しい朝の習慣として」）
   - 説明文2〜3文（50〜80字）：そのシーンでどう使うか・どんな気持ちになるかを情景描写
   ※「〇〇を使って」などの抽象的な表現は避け、具体的なシチュエーションを描写する

【商品情報】のuse_scenesにある内容を必ず使うこと。""",
    ),
    (
        "shopify_comparison_section_code",
        "SECTION_06_COMPARISON",
        """比較表セクション（見やすく）。<style>＋<section>。

構成：
1. 見出し：「他の方法との比較」
2. <table>形式：「従来の方法・競合」vs「【商品情報】の商品名」で比較
   比較項目4〜5行（【Core】のdifferentiationを参考に選定）：
   例：手軽さ / 継続しやすさ / プライバシー / コスト感 / 専門知識の必要性 など
   - 従来列：△または×＋短い補足テキスト
   - 商品列：◎＋短い強みテキスト（例：「自宅で完結」「一度の購入で」）
3. 表の下に免責文：「※比較はあくまで参考です。個人差があります。」

効果を断定しない表現にすること。""",
    ),
    (
        "shopify_faq_section_code",
        "SECTION_07_FAQ",
        """FAQセクション（5項目、details/summary開閉式）。<style>＋<section>。

構成：
1. 見出し：「よくあるご質問」
2. 5項目のFAQ：【Core】のpre_purchase_anxiety・purchase_barrierを元に商品固有の内容で生成
   各Q：【商品情報】の商品名を含めた具体的な質問（例：「〇〇は初めてでも使えますか？」）
   各A：2〜3文（50〜80字）で具体的に回答。断定表現は避ける

   必須テーマ（商品に合わせて言葉を調整）：
   Q1：はじめての方・使い方に関する不安
   Q2：使うタイミング・頻度に関する質問
   Q3：プライバシー・配送に関する質問
   Q4：他の方法・商品との併用
   Q5：効果の出方・継続について（「個人差があります」を含める）

details[open]時にsummary::after が「－」になるCSSを入れること。""",
    ),
    (
        "shopify_cta_section_code",
        "SECTION_08_CTA",
        """CTAセクション（自然な購入後押し）。<style>＋<section class="td-section td-cta">。

構成：
1. 見出し：背中をそっと押す一言（煽らない）
   【Core】のbrand_toneに合わせて「自分のペースで、はじめてみませんか」などのニュアンス
2. 本文2〜3文（60〜100字）：
   - 【商品情報】の商品名を自然に入れる
   - 【Core】のcta_policy・brand_toneに合わせた言葉選び
   - プライバシー配慮・安心感を含める
   - 「ぜひ」「今すぐ」「絶対」等の強い購買圧力ワードは使わない
3. 安心ワード（小さく）：「目立たない梱包でお届け」「ご自身のペースで」など1〜2点
4. 免責文（最小フォント）：「※個人差があります」

背景は必ず指定デザインのアクセントカラー、または var(--td-accent) を使うこと。
固定の緑色（#3d6b4fなど）や指定外の色を勝手に使わないこと。
テキストカラーは#ffffffまたはrgba(255,255,255,0.9)で白系にすること。""",
    ),
]


DEFAULT_DESIGN_OPTIONS = {
    "mood": "上品・信頼感",
    "palette": "ナチュラルグリーン",
    "background_color": "#faf8f4",
    "text_color": "#2b2b2b",
    "accent_color": "#3d6b4f",
    "card_color": "#ffffff",
    "border_color": "#e8e4de",
    "radius": "16px",
    "spacing": "ゆったり",
    "cta_strength": "控えめ",
    "target_market": "japan",
    "output_language": "ja",
    "market_note": "",
}


def _design_options(design_options: Optional[dict] = None) -> dict:
    opts = {**DEFAULT_DESIGN_OPTIONS, **(design_options or {})}
    for key in ("background_color", "text_color", "accent_color", "card_color", "border_color"):
        value = str(opts.get(key, "")).strip()
        opts[key] = value if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else DEFAULT_DESIGN_OPTIONS[key]
    opts["radius"] = str(opts.get("radius") or DEFAULT_DESIGN_OPTIONS["radius"]).strip()
    return opts


def _design_instructions(design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return (
        f"雰囲気:{opts['mood']} / パレット:{opts['palette']} / "
        f"背景:{opts['background_color']} / テキスト:{opts['text_color']} / "
        f"アクセント:{opts['accent_color']} / カード:{opts['card_color']} / "
        f"ボーダー:{opts['border_color']} / 角丸:{opts['radius']} / "
        f"余白:{opts['spacing']} / CTAの強さ:{opts['cta_strength']} / "
        f"構成:{opts.get('section_preset', '標準構成')} / "
        f"使用セクション:{'、'.join(opts.get('selected_sections', [])) if isinstance(opts.get('selected_sections'), list) else opts.get('selected_sections', '')}。"
        "この指定を最優先し、すべてのセクションで色・余白・トーンを統一すること。"
    )


def _market_options(options: Optional[dict] = None) -> dict:
    opts = options or {}
    target_market = str(opts.get("target_market") or opts.get("market") or "japan").strip().lower()
    output_language = str(opts.get("output_language") or "ja").strip().lower()
    if target_market not in {"japan", "us", "global"}:
        target_market = "japan"
    if output_language not in {"ja", "pt", "en"}:
        output_language = "ja"
    return {
        "target_market": target_market,
        "output_language": output_language,
        "market_note": str(opts.get("market_note") or "").strip(),
    }


def _market_instructions(options: Optional[dict] = None) -> str:
    opts = _market_options(options)
    market_label = {
        "japan": "Japan / Japanese e-commerce market",
        "us": "United States / US e-commerce market",
        "global": "Global / cross-border e-commerce",
    }[opts["target_market"]]
    lang_label = {
        "ja": "Japanese",
        "pt": "Portuguese (Brazil)",
        "en": "English",
    }[opts["output_language"]]
    compliance = {
        "japan": "薬機法・景表法リスクを避け、自然で丁寧な日本語表現にする。",
        "us": "Write for US consumers. Avoid FTC/FDA-sensitive claims, unsupported guarantees, medical promises, fake scarcity, and overclaiming. Use clear benefit-led English, practical objections, concise CTAs, and US-style ecommerce copy.",
        "global": "Use internationally understandable wording, avoid local legal overclaims, and keep claims evidence-aware and conservative.",
    }[opts["target_market"]]
    note = f"\n追加マーケット指示: {opts['market_note']}" if opts["market_note"] else ""
    return (
        f"販売先市場: {market_label}\n"
        f"出力言語: {lang_label}\n"
        f"入力言語に関係なく、生成結果本文・見出し・CTA・FAQ・SNS文は必ず出力言語で書くこと。\n"
        f"Markdownの見出し、表のラベル、制作メモ、注意点も、明示的に英語指定された画像AIプロンプト部分を除き、必ず出力言語で書くこと。\n"
        f"{compliance}{note}"
    )


def _fallback_css(design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return """<style>
:root,.td-product-page{--td-bg:%(background_color)s;--td-text:%(text_color)s;--td-accent:%(accent_color)s;--td-card:%(card_color)s;--td-border:%(border_color)s;--td-radius:%(radius)s;--td-font-lg:clamp(28px,4vw,48px);--td-font-md:clamp(24px,3vw,36px);--td-font-sm:clamp(18px,2vw,24px);--td-font-body:clamp(16px,1.4vw,18px);--td-space-y:80px}
.td-product-page,.td-section{font-family:inherit;color:var(--td-text,%(text_color)s)}
.td-section,.td-section *{box-sizing:border-box}
.td-section{width:100%%;background:var(--td-bg,%(background_color)s);padding:var(--td-space-y) 24px}
.td-container{width:100%%;max-width:1100px;margin:0 auto}
.td-badge{display:inline-flex;align-items:center;gap:6px;background:var(--td-accent,%(accent_color)s);color:#fff;padding:5px 14px;border-radius:999px;font-size:13px;font-weight:700;line-height:1.4}
.td-card{background:var(--td-card,%(card_color)s);border:1px solid var(--td-border,%(border_color)s);border-radius:var(--td-radius,%(radius)s)}
.td-btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:12px 22px;border-radius:999px;background:var(--td-accent,%(accent_color)s);color:#fff;text-decoration:none;font-weight:700}
@media(max-width:767px){.td-product-page{--td-space-y:52px}.td-section{padding:var(--td-space-y) 16px}.td-container{max-width:100%%}}
</style>""" % opts


def _fallback_hero(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    lang = _market_options(design_options)["output_language"]
    copy = {
        "ja": {
            "badge": "こだわりのアイテム",
            "headline": f"毎日に、{product_name}という選択を。",
            "sub": "生活の中に自然になじみ、自分のペースで続けられる一品です。",
            "benefits": ["自宅で手軽に使える", "日常習慣に馴染む設計", "丁寧な梱包でお届け"],
            "trust": "※個人差があります",
        },
        "pt": {
            "badge": "Item selecionado",
            "headline": f"Uma escolha mais simples para sua rotina: {product_name}.",
            "sub": "Feito para entrar no dia a dia com naturalidade, no seu ritmo.",
            "benefits": ["Fácil de usar em casa", "Pensado para a rotina", "Enviado com cuidado"],
            "trust": "*Os resultados podem variar.",
        },
        "en": {
            "badge": "Thoughtfully selected",
            "headline": f"Make {product_name} part of your routine.",
            "sub": "Designed to fit naturally into everyday life, at your own pace.",
            "benefits": ["Easy to use at home", "Built for daily routines", "Shipped with care"],
            "trust": "*Individual experiences may vary.",
        },
    }[lang]
    return f"""<style>
.td-hero{{background:var(--td-bg,{opts['background_color']});padding:80px 24px;text-align:center}}
.td-hero .td-container{{max-width:1100px;margin:0 auto}}
.td-hero .td-badge{{margin-bottom:24px}}
.td-hero h1{{font-size:clamp(28px,4vw,52px);color:var(--td-text,{opts['text_color']});font-weight:800;line-height:1.22;margin:0 0 16px}}
.td-hero-sub{{font-size:clamp(16px,1.6vw,20px);color:var(--td-text,{opts['text_color']});opacity:.78;line-height:1.8;margin:0 auto 40px;max-width:760px}}
.td-hero-benefits{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:0 0 28px}}
.td-hero-benefit{{background:var(--td-card,{opts['card_color']});border:1px solid var(--td-border,{opts['border_color']});border-radius:var(--td-radius,{opts['radius']});padding:16px 18px;font-size:clamp(15px,1.3vw,17px);color:var(--td-accent,{opts['accent_color']});font-weight:700;line-height:1.6}}
.td-hero-trust{{font-size:13px;color:var(--td-text,{opts['text_color']});opacity:.56;margin:0}}
@media(max-width:767px){{.td-hero{{padding:52px 16px}}.td-hero-benefits{{grid-template-columns:1fr}}}}
</style>
<section class="td-section td-hero">
  <div class="td-container">
    <span class="td-badge">{copy["badge"]}</span>
    <h1>{copy["headline"]}</h1>
    <p class="td-hero-sub">{copy["sub"]}</p>
    <div class="td-hero-benefits">
      <div class="td-hero-benefit">✓ {copy["benefits"][0]}</div>
      <div class="td-hero-benefit">✓ {copy["benefits"][1]}</div>
      <div class="td-hero-benefit">✓ {copy["benefits"][2]}</div>
    </div>
    <p class="td-hero-trust">{copy["trust"]}</p>
  </div>
</section>"""


def _fallback_about(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return f"""<style>
.td-about{{background:{opts['background_color']};padding:80px 24px}}
.td-about .td-container{{max-width:960px;margin:0 auto;text-align:center}}
.td-about h2{{font-size:clamp(24px,3vw,36px);color:{opts['text_color']};margin-bottom:16px}}
.td-about-lead{{font-size:clamp(16px,1.5vw,20px);color:{opts['text_color']};opacity:.78;line-height:1.9;margin-bottom:40px}}
.td-about-points{{display:flex;gap:20px;justify-content:center;flex-wrap:wrap}}
.td-about-point{{background:{opts['card_color']};border:1px solid {opts['border_color']};border-radius:{opts['radius']};padding:24px 28px;max-width:280px;text-align:left}}
.td-about-point h3{{font-size:clamp(16px,1.4vw,18px);color:{opts['accent_color']};margin-bottom:8px;font-weight:700}}
.td-about-point p{{font-size:clamp(15px,1.3vw,16px);color:{opts['text_color']};opacity:.75;line-height:1.8;margin:0}}
@media(max-width:767px){{.td-about{{padding:48px 16px}}.td-about-points{{flex-direction:column;align-items:center}}.td-about-point{{max-width:100%;width:100%}}}}
</style>
<section class="td-about">
  <div class="td-container">
    <h2>{product_name}について</h2>
    <p class="td-about-lead">毎日の生活に取り入れやすい設計で、様々な場面でご活用いただけます。</p>
    <div class="td-about-points">
      <div class="td-about-point"><h3>🌿 こんな方に</h3><p>生活の質を少し高めたい方、忙しい日々の中でも自分をケアしたい方に。</p></div>
      <div class="td-about-point"><h3>🏠 使える場面</h3><p>自宅でのリラックスタイムや、毎日のルーティンに無理なく組み込めます。</p></div>
      <div class="td-about-point"><h3>✨ 選ばれる理由</h3><p>使いやすさと品質を両立。はじめての方でも安心してお使いいただけます。</p></div>
    </div>
  </div>
</section>"""


def _fallback_problem(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return f"""<style>
.td-problem{{background:{opts['background_color']};padding:80px 24px}}
.td-problem .td-container{{max-width:960px;margin:0 auto}}
.td-problem h2{{font-size:clamp(24px,3vw,36px);color:{opts['text_color']};text-align:center;margin-bottom:48px}}
.td-problem-list{{list-style:none;padding:0;margin:0 0 40px;display:grid;gap:12px}}
.td-problem-list li{{background:{opts['card_color']};border-left:4px solid {opts['accent_color']};border-radius:{opts['radius']};padding:16px 20px;font-size:clamp(16px,1.4vw,18px);color:{opts['text_color']};opacity:.82;line-height:1.7}}
.td-problem-solution{{background:{opts['accent_color']};color:#fff;border-radius:{opts['radius']};padding:32px 36px;text-align:center}}
.td-problem-solution h3{{font-size:clamp(20px,2.2vw,26px);margin-bottom:12px}}
.td-problem-solution p{{font-size:clamp(16px,1.4vw,18px);line-height:1.8;opacity:.9;margin:0}}
@media(max-width:767px){{.td-problem{{padding:48px 16px}}.td-problem-solution{{padding:24px 20px}}}}
</style>
<section class="td-problem">
  <div class="td-container">
    <h2>こんなお悩みはありませんか？</h2>
    <ul class="td-problem-list">
      <li>😔 なかなか自分に合う方法が見つからない</li>
      <li>😔 続けたいけど手間がかかって挫折してしまう</li>
      <li>😔 プライバシーが気になって試しにくい</li>
      <li>😔 コストが気になって踏み出せない</li>
    </ul>
    <div class="td-problem-solution">
      <h3>そんな方に、{product_name}</h3>
      <p>自宅で、自分のペースで。無理なく始められて、続けやすい設計です。</p>
    </div>
  </div>
</section>"""


def _fallback_features(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return f"""<style>
.td-features{{background:{opts['background_color']};padding:80px 24px}}
.td-features .td-container{{max-width:1100px;margin:0 auto}}
.td-features h2{{font-size:clamp(24px,3vw,36px);color:{opts['text_color']};text-align:center;margin-bottom:48px}}
.td-features-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}}
.td-feature-card{{background:{opts['card_color']};border:1px solid {opts['border_color']};border-radius:{opts['radius']};padding:32px 24px;text-align:center}}
.td-feat-icon{{font-size:2.5rem;margin-bottom:16px}}
.td-feature-card h3{{font-size:clamp(17px,1.6vw,20px);color:{opts['accent_color']};margin-bottom:10px;font-weight:700}}
.td-feature-card p{{font-size:clamp(15px,1.3vw,16px);color:{opts['text_color']};opacity:.76;line-height:1.8;margin:0}}
@media(max-width:767px){{.td-features{{padding:48px 16px}}.td-features-grid{{grid-template-columns:1fr}}}}
</style>
<section class="td-features">
  <div class="td-container">
    <h2>{product_name}の特徴</h2>
    <div class="td-features-grid">
      <div class="td-feature-card"><div class="td-feat-icon">🏠</div><h3>自宅で使える</h3><p>特別な設備は不要。日常の中で手軽に取り入れられます。</p></div>
      <div class="td-feature-card"><div class="td-feat-icon">🔄</div><h3>続けやすい設計</h3><p>毎日の習慣に無理なく組み込める使いやすさにこだわっています。</p></div>
      <div class="td-feature-card"><div class="td-feat-icon">✨</div><h3>品質へのこだわり</h3><p>素材と製造工程にこだわり、安心してお使いいただける品質です。</p></div>
    </div>
  </div>
</section>"""


def _fallback_scenes(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return f"""<style>
.td-scenes{{background:{opts['background_color']};padding:80px 24px}}
.td-scenes .td-container{{max-width:1100px;margin:0 auto}}
.td-scenes h2{{font-size:clamp(24px,3vw,36px);color:{opts['text_color']};text-align:center;margin-bottom:48px}}
.td-scenes-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}}
.td-scene-card{{background:{opts['card_color']};border:1px solid {opts['border_color']};border-radius:{opts['radius']};padding:32px;}}
.td-scene-card .td-scene-icon{{font-size:2rem;margin-bottom:12px}}
.td-scene-card h3{{font-size:clamp(18px,2vw,22px);color:{opts['accent_color']};margin-bottom:8px}}
.td-scene-card p{{font-size:clamp(16px,1.4vw,18px);line-height:1.8;color:{opts['text_color']};opacity:.76;margin:0}}
@media(max-width:767px){{.td-scenes-grid{{grid-template-columns:1fr}}.td-scenes{{padding:48px 16px}}}}
</style>
<section class="td-scenes">
  <div class="td-container">
    <h2>こんなシーンで</h2>
    <div class="td-scenes-grid">
      <div class="td-scene-card"><div class="td-scene-icon">🏠</div><h3>自宅でのリラックスタイムに</h3><p>{product_name}は、自宅でゆったりと取り入れられます。特別な設備は必要ありません。</p></div>
      <div class="td-scene-card"><div class="td-scene-icon">🌙</div><h3>夜の習慣として</h3><p>就寝前のルーティンに加えるだけで、無理なく続けられます。</p></div>
      <div class="td-scene-card"><div class="td-scene-icon">🔒</div><h3>プライバシーを保ちながら</h3><p>自宅でひっそりと、自分のペースで続けられるのが魅力です。</p></div>
      <div class="td-scene-card"><div class="td-scene-icon">🎁</div><h3>大切な方へのギフトにも</h3><p>自分へのご褒美や、気遣いのあるプレゼントとしてもご利用いただけます。</p></div>
    </div>
  </div>
</section>"""


def _fallback_comparison(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return f"""<style>
.td-comparison{{background:{opts['background_color']};padding:80px 24px}}
.td-comparison .td-container{{max-width:960px;margin:0 auto}}
.td-comparison h2{{font-size:clamp(24px,3vw,36px);color:{opts['text_color']};text-align:center;margin-bottom:48px}}
.td-comp-table{{width:100%;border-collapse:collapse;background:{opts['card_color']};border-radius:{opts['radius']};overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.07)}}
.td-comp-table th{{background:{opts['accent_color']};color:#fff;padding:16px 20px;font-size:clamp(15px,1.3vw,17px);text-align:center}}
.td-comp-table td{{padding:16px 20px;border-bottom:1px solid {opts['border_color']};font-size:clamp(15px,1.3vw,17px);line-height:1.7;text-align:center}}
.td-comp-table tr:last-child td{{border-bottom:none}}
.td-comp-table td:first-child{{text-align:left;font-weight:600;color:{opts['text_color']}}}
.td-comp-check{{color:{opts['accent_color']};font-weight:700}}
.td-comp-x{{color:#aaa}}
@media(max-width:767px){{.td-comparison{{padding:48px 16px}}.td-comp-table th,.td-comp-table td{{padding:12px 10px;font-size:14px}}}}
</style>
<section class="td-comparison">
  <div class="td-container">
    <h2>他の方法との比較</h2>
    <table class="td-comp-table">
      <thead><tr><th>比較項目</th><th>通院・従来の方法</th><th>{product_name}</th></tr></thead>
      <tbody>
        <tr><td>自宅で使える</td><td class="td-comp-x">△</td><td class="td-comp-check">◎</td></tr>
        <tr><td>プライバシーが保たれる</td><td class="td-comp-x">△</td><td class="td-comp-check">◎</td></tr>
        <tr><td>自分のペースで続けられる</td><td class="td-comp-x">△</td><td class="td-comp-check">◎</td></tr>
        <tr><td>手軽に始められる</td><td class="td-comp-x">△</td><td class="td-comp-check">◎</td></tr>
        <tr><td>費用の目安</td><td>都度費用が発生</td><td>一度の購入で継続可能</td></tr>
      </tbody>
    </table>
    <p style="text-align:center;font-size:13px;color:#999;margin-top:16px">※個人差があります。効果を保証するものではありません。</p>
  </div>
</section>"""


def _fallback_faq(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    return f"""<style>
.td-faq{{background:{opts['background_color']};padding:80px 24px}}
.td-faq .td-container{{max-width:960px;margin:0 auto}}
.td-faq h2{{font-size:clamp(24px,3vw,36px);color:{opts['text_color']};text-align:center;margin-bottom:48px}}
.td-faq details{{background:{opts['card_color']};border:1px solid {opts['border_color']};border-radius:{opts['radius']};margin-bottom:12px;overflow:hidden}}
.td-faq summary{{padding:20px 24px;font-size:clamp(16px,1.4vw,18px);font-weight:600;cursor:pointer;list-style:none;color:{opts['text_color']}}}
.td-faq summary::after{{content:"＋";float:right;transition:.3s}}
.td-faq details[open] summary::after{{content:"－"}}
.td-faq .td-faq-body{{padding:0 24px 20px;font-size:clamp(16px,1.4vw,18px);line-height:1.8;color:{opts['text_color']};opacity:.75}}
@media(max-width:767px){{.td-faq{{padding:48px 16px}}.td-faq summary{{padding:16px}}.td-faq .td-faq-body{{padding:0 16px 16px}}}}
</style>
<section class="td-faq">
  <div class="td-container">
    <h2>よくある質問</h2>
    <details><summary>初めてでも使えますか？</summary><div class="td-faq-body">{product_name}は初めてご利用の方にもお使いいただきやすい設計です。詳しい使い方は同封の説明書をご確認ください。</div></details>
    <details><summary>どのタイミングで使うのがおすすめですか？</summary><div class="td-faq-body">就寝前や入浴後など、リラックスできる時間帯が特におすすめです。ご自身の生活リズムに合わせてお使いください。</div></details>
    <details><summary>周りに知られずに購入できますか？</summary><div class="td-faq-body">発送はプライバシーに配慮した梱包で行っております。外箱には内容物が分からないようにしてお届けします。</div></details>
    <details><summary>継続しやすいですか？</summary><div class="td-faq-body">毎日の習慣に無理なく取り入れていただけるよう設計されています。お客様ご自身のペースでご使用ください。</div></details>
    <details><summary>使用前に確認することはありますか？</summary><div class="td-faq-body">敏感肌の方やお体に気になる点がある方は、ご使用前に医師または薬剤師にご相談ください。</div></details>
  </div>
</section>"""


def _fallback_cta(product_name: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    lang = _market_options(design_options)["output_language"]
    copy = {
        "ja": {
            "headline": "自分のペースで、はじめてみませんか",
            "body": f"{product_name}は、毎日のルーティンにそっと寄り添うアイテムです。まずはご自身のペースでお試しください。",
            "note": "発送は目立たない梱包でプライバシーに配慮しています。※個人差があります。",
        },
        "pt": {
            "headline": "Comece no seu ritmo",
            "body": f"{product_name} foi pensado para acompanhar sua rotina com discrição e facilidade. Experimente no seu tempo.",
            "note": "Enviado com embalagem discreta. *Os resultados podem variar.",
        },
        "en": {
            "headline": "Start at your own pace",
            "body": f"{product_name} is designed to fit naturally into your routine. Try it in a way that feels right for you.",
            "note": "Ships in discreet packaging. *Individual experiences may vary.",
        },
    }[lang]
    return f"""<style>
.td-cta{{background:var(--td-accent,{opts['accent_color']});padding:80px 24px;text-align:center}}
.td-cta .td-container{{max-width:800px;margin:0 auto}}
.td-cta h2{{font-size:clamp(24px,3vw,36px);color:#fff;margin-bottom:16px}}
.td-cta p{{font-size:clamp(16px,1.5vw,19px);color:rgba(255,255,255,.9);line-height:1.8;margin:0 auto 26px;max-width:680px}}
.td-cta-note{{font-size:13px;color:rgba(255,255,255,.6);margin-top:24px}}
@media(max-width:767px){{.td-cta{{padding:56px 16px}}}}
</style>
<section class="td-section td-cta">
  <div class="td-container">
    <h2>{copy["headline"]}</h2>
    <p>{copy["body"]}</p>
    <p class="td-cta-note">{copy["note"]}</p>
  </div>
</section>"""


def _stabilize_shopify_section(key: str, code: str, design_options: Optional[dict] = None) -> str:
    opts = _design_options(design_options)
    if key == "shopify_common_css":
        return _fallback_css(opts)
    replacements = {
        "#3d6b4f": opts["accent_color"],
        "#3D6B4F": opts["accent_color"],
        "#faf8f4": opts["background_color"],
        "#FAF8F4": opts["background_color"],
        "#2b2b2b": opts["text_color"],
        "#2B2B2B": opts["text_color"],
        "#e8e4de": opts["border_color"],
        "#E8E4DE": opts["border_color"],
    }
    for before, after in replacements.items():
        code = code.replace(before, after)
    if key == "shopify_cta_section_code" and opts["accent_color"].lower() not in code.lower():
        code += (
            "\n<style>"
            f".td-cta{{background:var(--td-accent,{opts['accent_color']})!important}}"
            "</style>"
        )
    return code


class GeneratorEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_product_page(self, core: str, product_info: dict, generation_options: Optional[dict] = None) -> str:
        info_text = "\n".join(f"- {k}: {v}" for k, v in product_info.items() if v)
        prompt = PRODUCT_PAGE_PROMPT.format(core=core, product_info=info_text)
        prompt += "\n\n【販売先・出力言語】\n" + _market_instructions(generation_options)
        return self.llm.generate_structured(prompt)

    def generate_image_prompts(self, core: str, product_name: str, category: str) -> str:
        prompt = IMAGE_PROMPT_PROMPT.format(
            core=core, product_name=product_name, category=category
        )
        return self.llm.generate_structured(prompt)

    def generate_video_scripts(self, core: str, product_name: str) -> str:
        prompt = VIDEO_SCRIPT_PROMPT.format(core=core, product_name=product_name)
        return self.llm.generate_structured(prompt)

    def generate_sns_content(self, core: str, product_name: str) -> str:
        prompt = SNS_PROMPT.format(core=core, product_name=product_name)
        return self.llm.generate_structured(prompt)

    def generate_custom_liquid(self, core: str, product_info: dict, design_options: Optional[dict] = None) -> str:
        prompt = CUSTOM_LIQUID_PROMPT.format(
            core=core,
            product_name=product_info.get("name", ""),
            category=product_info.get("category", ""),
            price=product_info.get("price", ""),
            description=product_info.get("description", ""),
            features=product_info.get("features", ""),
            target=product_info.get("target", ""),
            use_scenes=product_info.get("use_scenes", ""),
            design_instructions=_design_instructions(design_options),
            market_instructions=_market_instructions(design_options),
        )
        return self.llm.generate_structured(prompt, max_tokens=8192)

    def _generate_one_section(
        self, key: str, marker: str, instructions: str, args: dict, fallback_fn
    ) -> str:
        prompt = _SECTION_BASE_PROMPT.format(
            marker=marker, instructions=instructions, **args
        )
        try:
            raw = self.llm.generate_structured(prompt, max_tokens=4096)
            # LLMClient returns errors as strings (e.g. "[Anthropic APIエラー：...]")
            # rather than raising exceptions — detect and fall back
            if not raw or raw.lstrip().startswith("[") or "<" not in raw:
                return fallback_fn()
            m = re.search(rf"<<<{marker}>>>(.*?)<<<END_SECTION>>>", raw, re.DOTALL)
            code = m.group(1).strip() if m else raw.strip()
            return code if code else fallback_fn()
        except Exception:
            return fallback_fn()

    def generate_shopify_sections(self, core: str, product_info: dict, design_options: Optional[dict] = None) -> dict:
        product_name = product_info.get("name", "")
        design_options = _design_options(design_options)
        # Truncate core to avoid 400 "prompt too long" errors from the API
        core_trimmed = core[:3500] if len(core) > 3500 else core
        args = dict(
            rules=_SHOPIFY_RULES.format(
                design_instructions=_design_instructions(design_options),
                market_instructions=_market_instructions(design_options),
            ),
            market_context=_market_instructions(design_options),
            core=core_trimmed,
            product_name=product_name,
            category=product_info.get("category", ""),
            price=product_info.get("price", ""),
            description=product_info.get("description", ""),
            features=product_info.get("features", ""),
            target=product_info.get("target", ""),
            use_scenes=product_info.get("use_scenes", ""),
        )
        fallbacks = {
            "shopify_common_css":               lambda: _fallback_css(design_options),
            "shopify_hero_section_code":        lambda: _fallback_hero(product_name, design_options),
            "shopify_about_section_code":       lambda: _fallback_about(product_name, design_options),
            "shopify_problem_section_code":     lambda: _fallback_problem(product_name, design_options),
            "shopify_features_section_code":    lambda: _fallback_features(product_name, design_options),
            "shopify_usage_scene_section_code": lambda: _fallback_scenes(product_name, design_options),
            "shopify_comparison_section_code":  lambda: _fallback_comparison(product_name, design_options),
            "shopify_faq_section_code":         lambda: _fallback_faq(product_name, design_options),
            "shopify_cta_section_code":         lambda: _fallback_cta(product_name, design_options),
        }
        sections = {}
        for key, marker, instructions in SHOPIFY_SECTION_CONFIGS:
            if key == "shopify_common_css":
                sections[key] = _fallback_css(design_options)
                continue
            if key == "shopify_hero_section_code":
                sections[key] = _fallback_hero(product_name, design_options)
                continue
            generated = self._generate_one_section(
                key, marker, instructions, args, fallbacks[key]
            )
            sections[key] = _stabilize_shopify_section(key, generated, design_options)
        return sections

    # ── Per-item generation ───────────────────────────────────────────────────

    def _quality_instruction(self, quality_options) -> str:
        if not quality_options:
            return "指定なし"
        market_text = _market_instructions(quality_options)
        return (
            f"用途: {quality_options.get('purpose') or '指定なし'}\n"
            f"雰囲気: {quality_options.get('tone') or '指定なし'}\n"
            f"訴求の強さ: {quality_options.get('strength') or '標準'}\n"
            f"追加指示: {quality_options.get('note') or 'なし'}\n"
            f"{market_text}"
        )

    def generate_image_prompt_item(self, item_key: str, core: str,
                                   product_name: str, category: str,
                                   quality_options=None) -> str:
        _cfg = {
            "main_visual":  ("商品ページ メインビジュアル", "白背景またはクリーンな背景で商品全体を美しく。高級感と信頼感を演出。"),
            "product_only": ("商品単体画像", "様々な角度の商品単体カット。素材・質感が伝わる接写も含める。"),
            "usage_scene":  ("使用シーン画像", "実際の使用シーン・ライフスタイルカット。ターゲットが共感できる場面。"),
            "benefit":      ("ベネフィット訴求画像", "主なベネフィット・効果を視覚的に表現。Before/After的な表現も効果的。"),
            "comparison":   ("比較画像", "競合との差別化ポイントを視覚化。"),
            "ad_banner":    ("広告バナー画像", "クリック率重視。商品＋キャッチコピーが映える広告バナー構成。"),
            "sns_post":     ("SNS投稿画像", "Instagram等SNS向け。1:1または4:5サイズ。"),
            "story":        ("ストーリー用画像", "Instagram/TikTokストーリー向け縦型(9:16)。全画面を活かした構成。"),
        }
        cfg = _cfg.get(item_key)
        if not cfg:
            return f"[未知の項目: {item_key}]"
        item_name, instructions = cfg
        quality_text = self._quality_instruction(quality_options)
        prompt = (
            f"あなたは画像生成AIのプロンプト作成専門家です。\n"
            f"以下のCoreと商品情報をもとに、「{item_name}」の画像生成プロンプトを作成してください。\n\n"
            f"【Core】\n{core[:2000]}\n\n"
            f"【商品情報】\n商品名: {product_name}\nカテゴリ: {category}\n\n"
            f"【この画像の目的・要件】\n{instructions}\n\n"
            f"【今回の生成方向性】\n{quality_text}\n\n"
            f"【出力形式】\n"
            f"## {item_name}\n\n"
            f"### 使う場所\n"
            f"### 推奨比率\n"
            f"### 目的\n"
            f"### 構図・アングル\n"
            f"### 背景・セッティング\n"
            f"### ライティング\n"
            f"### カラーパレット\n"
            f"### 雰囲気・スタイル\n"
            f"### 商品の見せ方\n"
            f"### 入れると良いテキスト\n"
            f"### NG要素\n\n"
            f"### 生成AIプロンプト（英語）\n"
            f"（Midjourney/Stable Diffusion等に直接貼り付けられる英語プロンプト）\n\n"
            f"### 制作メモ（出力言語）\n\n"
            f"重要:\n"
            f"- 生成AIプロンプトは英語で、被写体・構図・レンズ感・光・質感・背景・色を具体的に書く。\n"
            f"- 生成AIプロンプト以外の説明、見出し、制作メモは出力言語で書く。\n"
            f"- 商品そのものを曖昧にせず、販売先市場のECで信頼される清潔感と質感を出す。\n"
            f"- 効果保証、医療的断定、過度なBefore/After表現は避ける。\n"
            f"- そのまま貼れる完成プロンプトとして出す。"
        )
        return self.llm.generate_structured(prompt)

    def generate_video_script_item(self, item_key: str, core: str, product_name: str,
                                   quality_options=None) -> str:
        _cfg = {
            "script_15s": ("15秒動画台本", "フック(3秒)→悩み提示(4秒)→商品紹介(5秒)→CTA(3秒)の構成。"),
            "script_30s": ("30秒動画台本", "フック→悩み→ベネフィット→安心材料→CTAの流れ。"),
            "script_45s": ("45秒動画台本", "複数ベネフィットと安心材料を詳しく展開できる45秒構成。"),
            "script_60s": ("60秒動画台本", "完結したストーリーを展開。YouTube Shorts向け。"),
            "tiktok":     ("TikTok用台本", "TikTokのトレンドに合わせた台本。音楽・エフェクト・テキストオーバーレイの使い方も含む。"),
            "reels":      ("Instagram Reels用台本", "ビジュアル重視のReels台本。ブランドトーンと映像美を両立。"),
            "yt_shorts":  ("YouTube Shorts用台本", "縦型・教育的なYouTube Shorts台本。"),
            "narration":  ("読み上げ用ナレーション", "ナレーション音声テキストのみ。自然で読み上げやすい日本語。"),
            "timeline":   ("秒数別構成", "秒数ごとの映像・テキスト・音声・テロップを一覧化した構成表。"),
            "telop":      ("テロップ版", "画面表示テロップ（字幕）テキストのみ。端的で読みやすい文言。"),
            "shooting":   ("撮影指示付き台本", "カメラアングル・照明・小道具・演出指示を含む詳細な撮影台本。"),
        }
        cfg = _cfg.get(item_key)
        if not cfg:
            return f"[未知の項目: {item_key}]"
        item_name, instructions = cfg
        quality_text = self._quality_instruction(quality_options)
        prompt = (
            f"あなたは動画台本の専門家です。\n"
            f"以下のCoreをもとに、「{item_name}」を作成してください。\n\n"
            f"【Core】\n{core[:2000]}\n\n"
            f"【商品情報】\n商品名: {product_name}\n\n"
            f"【この台本の要件】\n{instructions}\n\n"
            f"【今回の生成方向性】\n{quality_text}\n\n"
            f"【出力形式】\n"
            f"## {item_name}\n"
            f"### 狙い\n"
            f"### 冒頭3秒フック\n"
            f"### 完成台本\n"
            f"### ナレーション\n"
            f"### テロップ\n"
            f"### 映像・撮影指示\n"
            f"### CTA案\n"
            f"### NG表現・注意点\n\n"
            f"重要:\n"
            f"- 冒頭3秒のフックを最優先する。\n"
            f"- 視聴維持のため、1カットの意図が分かるようにする。\n"
            f"- 出力言語に合わせ、押し売り感を避ける。\n"
            f"- 販売先市場の広告審査・法規制で問題になりやすい表現、効果保証、断定表現は避ける。"
        )
        return self.llm.generate_structured(prompt)

    def generate_video_script_combo(self, duration_key: str, type_key: str,
                                    core: str, product_name: str,
                                    quality_options=None) -> str:
        _duration_cfg = {
            "15s": ("15秒", "0〜3秒: 強いフック / 4〜8秒: 悩み提示 / 9〜12秒: 商品ベネフィット / 13〜15秒: CTA"),
            "30s": ("30秒", "0〜3秒: フック / 4〜10秒: 悩み・共感 / 11〜20秒: 商品紹介・ベネフィット / 21〜27秒: 安心材料 / 28〜30秒: CTA"),
            "45s": ("45秒", "0〜4秒: フック / 5〜14秒: 悩み・背景 / 15〜30秒: ベネフィット詳細 / 31〜40秒: 使用シーン・安心材料 / 41〜45秒: CTA"),
            "60s": ("60秒", "0〜5秒: フック / 6〜15秒: 悩み・共感 / 16〜35秒: 商品紹介・ベネフィット詳細 / 36〜50秒: 安心材料・FAQ / 51〜60秒: CTA"),
        }
        _type_cfg = {
            "tiktok": ("TikTok用台本", "TikTokらしいテンポ、冒頭の違和感・共感フック、短いカット割り、テキストオーバーレイを重視。"),
            "reels": ("Instagram Reels用台本", "見た目の清潔感、ブランド感、保存したくなるベネフィット整理、自然な導線を重視。"),
            "yt_shorts": ("YouTube Shorts用台本", "短尺でも理解しやすい教育・比較・レビュー型の流れを重視。"),
            "ad_script": ("広告用台本", "広告配信で使いやすい問題提起、商品理解、購入前不安の解消、CTAを重視。"),
            "narration": ("読み上げナレーション", "音声収録しやすい自然な口語。映像指示よりも読み上げ本文を中心にする。"),
            "timeline": ("秒数別構成", "秒数ごとの映像、テロップ、ナレーション、目的を表形式で整理する。"),
            "shooting": ("撮影指示付き台本", "カメラアングル、手元カット、照明、小道具、商品の見せ方まで具体的に指示する。"),
            "higgs_marketing_studio": (
                "Higgs Marketing Studio用プロンプト",
                "Higgs Marketing Studioに貼り付けて動画生成・広告素材生成に使える完成プロンプトを作る。"
            ),
        }
        duration_label, duration_structure = _duration_cfg.get(duration_key, (duration_key, "選択された秒数に合わせて構成する。"))
        type_label, type_instruction = _type_cfg.get(type_key, (type_key, "選択された生成タイプに合わせて作成する。"))
        quality_text = self._quality_instruction(quality_options)

        if type_key == "higgs_marketing_studio":
            prompt = (
                f"あなたはHiggs Marketing Studio向けの動画生成プロンプト設計者です。\n"
                f"以下のCoreをもとに、{duration_label}の広告・SNS動画を作るための"
                f"Marketing Studio用プロンプトを完成させてください。\n\n"
                f"【Core】\n{core[:2200]}\n\n"
                f"【商品情報】\n商品名: {product_name}\n\n"
                f"【尺】{duration_label}\n"
                f"【推奨構成】{duration_structure}\n\n"
                f"【今回の生成方向性】\n{quality_text}\n\n"
                f"【出力形式】\n"
                f"## Higgs Marketing Studio Prompt\n"
                f"- Objective:\n- Video Length:\n- Aspect Ratio:\n- Target Audience:\n"
                f"- Main Hook:\n- Scene-by-scene Direction:\n- Visual Style:\n"
                f"- Product Presentation:\n- On-screen Text:\n- Voiceover Script:\n"
                f"- Music / Sound:\n- CTA:\n- Negative Instructions:\n\n"
                f"### 制作メモ（出力言語）\n\n"
                f"重要:\n"
                f"- Marketing Studioに貼り付けやすいよう、英語中心で具体的に書く。\n"
                f"- カット、画角、光、商品接写、手元動作、画面テキストまで指定する。\n"
                f"- 補足メモ、説明、注意点は出力言語に合わせる。\n"
                f"- 販売先市場の広告審査・法規制で問題になりやすい表現は避ける。"
            )
            return self.llm.generate_structured(prompt)

        prompt = (
            f"あなたは動画台本の専門家です。\n"
            f"以下のCoreをもとに、「{duration_label} × {type_label}」を作成してください。\n\n"
            f"【Core】\n{core[:2200]}\n\n"
            f"【商品情報】\n商品名: {product_name}\n\n"
            f"【尺】{duration_label}\n"
            f"【秒数構成】{duration_structure}\n"
            f"【生成タイプ】{type_label}\n"
            f"【タイプ別要件】{type_instruction}\n\n"
            f"【今回の生成方向性】\n{quality_text}\n\n"
            f"【出力形式】\n"
            f"## {duration_label} × {type_label}\n\n"
            f"### 狙い\n"
            f"### 冒頭3秒フック\n"
            f"### 秒数別構成\n"
            f"### 完成台本\n"
            f"### ナレーション\n"
            f"### テロップ\n"
            f"### 映像・撮影指示\n"
            f"### フック案 3つ\n"
            f"### CTA案 3つ\n"
            f"### NG表現・注意点\n\n"
            f"重要:\n"
            f"- 冒頭3秒のフックを特に強くする。\n"
            f"- 秒数別構成は、映像・テロップ・ナレーション・目的が分かる表にする。\n"
            f"- ターゲットが自分ごと化できる悩み、使用シーン、安心材料を入れる。\n"
            f"- 出力言語に合わせた自然で親しみやすい表現。押しつけがましくしない。\n"
            f"- 販売先市場の広告審査・法規制で問題になりやすい表現、効果保証、断定表現は避ける。"
        )
        return self.llm.generate_structured(prompt)

    def generate_ads_sns_item(self, media: str, content_type: str,
                              core: str, product_name: str,
                              quality_options=None) -> str:
        _media_labels = {
            "instagram": "Instagram", "tiktok": "TikTok",
            "yt_shorts": "YouTube Shorts", "facebook": "Facebook",
            "x": "X (Twitter)", "line": "LINE",
            "shopify_ad": "Shopify広告文", "google_ad": "Google広告",
        }
        _type_labels = {
            "post": "投稿文", "ad_copy": "広告コピー", "caption": "キャプション",
            "hashtag": "ハッシュタグ", "cta": "CTA", "hook": "短いフック",
            "comment_bait": "コメント誘導文",
        }
        media_label = _media_labels.get(media, media)
        type_label = _type_labels.get(content_type, content_type)
        quality_text = self._quality_instruction(quality_options)
        prompt = (
            f"あなたはSNS・広告マーケティングの専門家です。\n"
            f"以下のCoreをもとに、{media_label}向けの「{type_label}」を3〜5案作成してください。\n\n"
            f"【Core】\n{core[:2000]}\n\n"
            f"【商品情報】\n商品名: {product_name}\n\n"
            f"【媒体】{media_label}\n【生成タイプ】{type_label}\n\n"
            f"【今回の生成方向性】\n{quality_text}\n\n"
            f"【出力形式】\n"
            f"## {media_label} / {type_label}\n"
            f"### 使いどころ\n"
            f"### 案1\n"
            f"### 案2\n"
            f"### 案3\n"
            f"### 短縮版\n"
            f"### CTA\n"
            f"### 注意点\n\n"
            f"重要:\n"
            f"- {media_label}のトーン・文化・文字数制限に合わせる。\n"
            f"- 最初の1行でスクロールを止める。\n"
            f"- 商品名または商品の特徴が自然に入るようにする。\n"
            f"- 絵文字は媒体に合う範囲で使いすぎない。\n"
            f"- 販売先市場の広告審査・法規制で問題になりやすい表現、効果保証、断定表現は避ける。"
        )
        return self.llm.generate_structured(prompt)

    def improve_generated_content(self, content: str, core: str, content_type: str,
                                  improve_mode: str, check_notes: str = "",
                                  generation_options=None) -> str:
        mode_instructions = {
            "shorten": "内容の要点を残しながら、短く読みやすくする。",
            "natural": "不自然な表現を直し、指定された販売先市場と出力言語に合う自然な表現にする。",
            "premium": "安っぽさを消し、上品・信頼感・高級感が伝わる表現にする。",
            "ad_strong": "誇大表現を避けながら、広告・SNS向けに冒頭フックとCTAを強くする。",
            "risk_safe": "薬機法・景表法リスク、効果保証、断定表現を弱めて安全な表現にする。",
            "higgs": "Higgs Marketing Studioや画像・動画生成AIに貼りやすい、具体的なプロンプトへ整える。",
            "from_checks": "チェック結果の指摘を反映して、品質と安全性を改善する。",
        }
        instruction = mode_instructions.get(improve_mode, improve_mode)
        prompt = (
            f"あなたはShopify商品ページ・広告・SNS制作の編集責任者です。\n"
            f"以下の生成結果を改善してください。\n\n"
            f"【コンテンツ種別】\n{content_type}\n\n"
            f"【改善方針】\n{instruction}\n\n"
            f"【Core】\n{core[:2200]}\n\n"
            f"【チェック結果・修正メモ】\n{check_notes or 'なし'}\n\n"
            f"【元の生成結果】\n{content}\n\n"
            f"【販売先・出力言語】\n{_market_instructions(generation_options)}\n\n"
            f"【出力ルール】\n"
            f"- 元のMarkdown見出し構造はできるだけ維持する。\n"
            f"- 画像プロンプトの場合、英語プロンプト部分は英語のまま具体化する。\n"
            f"- 動画台本の場合、冒頭3秒・ナレーション・テロップ・撮影指示を分かりやすくする。\n"
            f"- SNS/広告の場合、冒頭1行とCTAを強くする。\n"
            f"- 薬機法・景表法リスク、医療的断定、効果保証、過度なBefore/After表現は避ける。\n"
            f"- 改善後の完成版だけを出力する。説明文や前置きは不要。"
        )
        return self.llm.generate_structured(prompt)
