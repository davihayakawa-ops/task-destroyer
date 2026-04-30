import re
from .llm_client import LLMClient

PRODUCT_PAGE_PROMPT = """
あなたはShopify商品ページ制作の専門家です。
以下のCoreをベースに、日本市場向けの商品ページコンテンツを生成してください。

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
- 日本市場向けの自然で上品な日本語を使うこと
- 断定表現・医療的表現は避けること
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
日本市場向けの美的感覚（清潔感、上品さ、信頼感）を反映すること。
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
- 日本語は自然で柔らかい表現にすること
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
- 日本語は自然で丁寧な表現にする

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
- 背景色: #faf8f4（温かみのあるオフホワイト）
- テキスト色: #2b2b2b
- アクセントカラー: #3d6b4f（落ち着いたグリーン）
- 角丸: 14px〜18px
- 余白はゆったりとる
- カードには薄いボーダー (#eee) と白背景

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
- 日本語は自然で親しみやすくすること
- 絵文字は適度に使うこと
- 商品の魅力を短く伝えること
"""


_SHOPIFY_RULES = """【共通ルール】
- <html><head><body>タグ不要 / JavaScriptなし / 外部CSS・ライブラリなし
- 全CSSクラス名は必ず「td-」プレフィックス
- @media(max-width:767px) でスマホ対応
- 薬機法・景表法リスク表現禁止（「治る」「必ず」「確実に」「医学的に証明」等）
- コードのみ出力。マークダウン(```)や説明文は不要
【フォント】大見出し:clamp(28px,4vw,48px) / セクション見出し:clamp(24px,3vw,36px) / 小見出し:clamp(18px,2vw,24px) / 本文:clamp(16px,1.4vw,18px);line-height:1.8
【レイアウト】max-width:1100px;margin:0 auto;padding:80px 24px → スマホ:padding:48px 16px
【デザイン】背景:#faf8f4 / テキスト:#2b2b2b / アクセント:#3d6b4f / カード:#fff;border:1px solid #e8e4de;border-radius:16px
各セクションは<style>タグを含む単体で動作するコードにする。"""

_SECTION_BASE_PROMPT = """あなたはShopifyのカスタムLiquid制作の専門家です。
1つのセクションのHTMLコードのみを生成してください。
{rules}
【Core】
{core}

【商品情報】
商品名:{product_name} / カテゴリ:{category} / 価格:{price}
説明:{description}
特徴:{features} / ターゲット:{target} / 使用シーン:{use_scenes}

以下のマーカーで囲んで出力してください（マーカー行はそのまま出力）：

<<<{marker}>>>
{instructions}
<<<END_SECTION>>>"""

SHOPIFY_SECTION_CONFIGS = [
    (
        "shopify_common_css",
        "SECTION_00_COMMON_CSS",
        ":root CSS変数（--td-bg:#faf8f4 / --td-text:#2b2b2b / --td-accent:#3d6b4f / --td-radius:16px）"
        "＋ .td-section / .td-container / .td-badge の基本クラス定義。<style>タグのみ。<section>タグは含めない。",
    ),
    (
        "shopify_hero_section_code",
        "SECTION_01_HERO",
        "ファーストビュー：カテゴリバッジ＋キャッチコピー(H1)＋サブコピー＋ベネフィット3点（チェックマーク付きカード）＋信頼バッジ。<style>＋<section>。",
    ),
    (
        "shopify_about_section_code",
        "SECTION_02_ABOUT",
        "商品について：商品概要テキスト＋「誰のための商品か」＋「どんな場面で使えるか」を3カラムカードで紹介。<style>＋<section>。",
    ),
    (
        "shopify_problem_section_code",
        "SECTION_03_PROBLEM",
        "悩み・共感：ターゲットの悩みリスト（絵文字付き4〜5項目）＋この商品が解決策になる理由（緑背景のハイライトボックス）。<style>＋<section>。",
    ),
    (
        "shopify_features_section_code",
        "SECTION_04_FEATURES",
        "特徴カード：3〜5個のカード形式（大きな絵文字＋太字見出し＋説明文）。CSS Grid 3列→スマホ1列。<style>＋<section>。",
    ),
    (
        "shopify_usage_scene_section_code",
        "SECTION_05_SCENES",
        "使用シーン：自宅・夜の習慣・日常習慣・プレゼント等の視点で2〜4シーン。各シーンにアイコン＋見出し＋説明。2列グリッド。<style>＋<section>。",
    ),
    (
        "shopify_comparison_section_code",
        "SECTION_06_COMPARISON",
        "比較表：「従来の方法」vs「この商品」で手軽さ・継続性・プライバシー・コストを<table>形式で比較。効果を断定しない表現。<style>＋<section>。",
    ),
    (
        "shopify_faq_section_code",
        "SECTION_07_FAQ",
        "FAQ（details/summary開閉式、5〜7項目）：初めてでも使えるか・タイミング・プライバシー・継続性・注意事項など。<style>＋<section>。",
    ),
    (
        "shopify_cta_section_code",
        "SECTION_08_CTA",
        "CTA：煽らず自然な購入後押し。「自分のペースで始められる」ニュアンス。安心感・プライバシー配慮を含む。緑背景で目立たせる。<style>＋<section>。",
    ),
]


def _fallback_css() -> str:
    return """<style>
:root{--td-bg:#faf8f4;--td-text:#2b2b2b;--td-accent:#3d6b4f;--td-card:#fff;--td-border:#e8e4de;--td-radius:16px;--td-font-lg:clamp(28px,4vw,48px);--td-font-md:clamp(24px,3vw,36px);--td-font-sm:clamp(18px,2vw,24px);--td-font-body:clamp(16px,1.4vw,18px)}
.td-section{background:var(--td-bg);padding:80px 24px}
.td-container{max-width:1100px;margin:0 auto}
.td-badge{display:inline-block;background:var(--td-accent);color:#fff;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600;letter-spacing:.05em}
@media(max-width:767px){.td-section{padding:48px 16px}}
</style>"""


def _fallback_hero(product_name: str) -> str:
    return f"""<style>
.td-hero{{background:linear-gradient(135deg,#faf8f4 0%,#f0ece4 100%);padding:80px 24px;text-align:center}}
.td-hero .td-container{{max-width:1100px;margin:0 auto}}
.td-hero .td-badge{{margin-bottom:24px;display:inline-block}}
.td-hero h1{{font-size:clamp(28px,4vw,52px);color:#2b2b2b;font-weight:700;line-height:1.3;margin-bottom:16px}}
.td-hero-sub{{font-size:clamp(16px,1.6vw,20px);color:#5a5a5a;line-height:1.8;margin-bottom:48px}}
.td-hero-benefits{{display:flex;justify-content:center;gap:20px;flex-wrap:wrap;margin-bottom:40px}}
.td-hero-benefit{{background:#fff;border:1px solid #e8e4de;border-radius:12px;padding:14px 22px;font-size:clamp(15px,1.3vw,17px);color:#3d6b4f;font-weight:600}}
.td-hero-trust{{font-size:13px;color:#aaa}}
@media(max-width:767px){{.td-hero{{padding:48px 16px}}.td-hero-benefits{{flex-direction:column;align-items:center}}.td-hero-benefit{{width:100%;text-align:center}}}}
</style>
<section class="td-hero">
  <div class="td-container">
    <span class="td-badge">こだわりのアイテム</span>
    <h1>{product_name}</h1>
    <p class="td-hero-sub">毎日の生活に、ちょっとした豊かさを。<br>自分のペースで、無理なく続けられる一品です。</p>
    <div class="td-hero-benefits">
      <div class="td-hero-benefit">✓ 自宅で手軽に使える</div>
      <div class="td-hero-benefit">✓ 日常習慣に馴染む設計</div>
      <div class="td-hero-benefit">✓ 丁寧な梱包でお届け</div>
    </div>
    <p class="td-hero-trust">※個人差があります</p>
  </div>
</section>"""


def _fallback_about(product_name: str) -> str:
    return f"""<style>
.td-about{{background:#faf8f4;padding:80px 24px}}
.td-about .td-container{{max-width:960px;margin:0 auto;text-align:center}}
.td-about h2{{font-size:clamp(24px,3vw,36px);color:#2b2b2b;margin-bottom:16px}}
.td-about-lead{{font-size:clamp(16px,1.5vw,20px);color:#5a5a5a;line-height:1.9;margin-bottom:40px}}
.td-about-points{{display:flex;gap:20px;justify-content:center;flex-wrap:wrap}}
.td-about-point{{background:#fff;border:1px solid #e8e4de;border-radius:14px;padding:24px 28px;max-width:280px;text-align:left}}
.td-about-point h3{{font-size:clamp(16px,1.4vw,18px);color:#3d6b4f;margin-bottom:8px;font-weight:700}}
.td-about-point p{{font-size:clamp(15px,1.3vw,16px);color:#5a5a5a;line-height:1.8;margin:0}}
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


def _fallback_problem(product_name: str) -> str:
    return f"""<style>
.td-problem{{background:#f3f0eb;padding:80px 24px}}
.td-problem .td-container{{max-width:960px;margin:0 auto}}
.td-problem h2{{font-size:clamp(24px,3vw,36px);color:#2b2b2b;text-align:center;margin-bottom:48px}}
.td-problem-list{{list-style:none;padding:0;margin:0 0 40px;display:grid;gap:12px}}
.td-problem-list li{{background:#fff;border-left:4px solid #e0d8cf;border-radius:8px;padding:16px 20px;font-size:clamp(16px,1.4vw,18px);color:#5a5a5a;line-height:1.7}}
.td-problem-solution{{background:#3d6b4f;color:#fff;border-radius:16px;padding:32px 36px;text-align:center}}
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


def _fallback_features(product_name: str) -> str:
    return f"""<style>
.td-features{{background:#faf8f4;padding:80px 24px}}
.td-features .td-container{{max-width:1100px;margin:0 auto}}
.td-features h2{{font-size:clamp(24px,3vw,36px);color:#2b2b2b;text-align:center;margin-bottom:48px}}
.td-features-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}}
.td-feature-card{{background:#fff;border:1px solid #e8e4de;border-radius:16px;padding:32px 24px;text-align:center}}
.td-feat-icon{{font-size:2.5rem;margin-bottom:16px}}
.td-feature-card h3{{font-size:clamp(17px,1.6vw,20px);color:#3d6b4f;margin-bottom:10px;font-weight:700}}
.td-feature-card p{{font-size:clamp(15px,1.3vw,16px);color:#5a5a5a;line-height:1.8;margin:0}}
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


def _fallback_scenes(product_name: str) -> str:
    return f"""<style>
.td-scenes{{background:#faf8f4;padding:80px 24px}}
.td-scenes .td-container{{max-width:1100px;margin:0 auto}}
.td-scenes h2{{font-size:clamp(24px,3vw,36px);color:#2b2b2b;text-align:center;margin-bottom:48px}}
.td-scenes-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}}
.td-scene-card{{background:#fff;border:1px solid #e8e4de;border-radius:16px;padding:32px;}}
.td-scene-card .td-scene-icon{{font-size:2rem;margin-bottom:12px}}
.td-scene-card h3{{font-size:clamp(18px,2vw,22px);color:#3d6b4f;margin-bottom:8px}}
.td-scene-card p{{font-size:clamp(16px,1.4vw,18px);line-height:1.8;color:#5a5a5a;margin:0}}
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


def _fallback_comparison(product_name: str) -> str:
    return f"""<style>
.td-comparison{{background:#f3f0eb;padding:80px 24px}}
.td-comparison .td-container{{max-width:960px;margin:0 auto}}
.td-comparison h2{{font-size:clamp(24px,3vw,36px);color:#2b2b2b;text-align:center;margin-bottom:48px}}
.td-comp-table{{width:100%;border-collapse:collapse;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.07)}}
.td-comp-table th{{background:#3d6b4f;color:#fff;padding:16px 20px;font-size:clamp(15px,1.3vw,17px);text-align:center}}
.td-comp-table td{{padding:16px 20px;border-bottom:1px solid #e8e4de;font-size:clamp(15px,1.3vw,17px);line-height:1.7;text-align:center}}
.td-comp-table tr:last-child td{{border-bottom:none}}
.td-comp-table td:first-child{{text-align:left;font-weight:600;color:#2b2b2b}}
.td-comp-check{{color:#3d6b4f;font-weight:700}}
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


def _fallback_faq(product_name: str) -> str:
    return f"""<style>
.td-faq{{background:#faf8f4;padding:80px 24px}}
.td-faq .td-container{{max-width:960px;margin:0 auto}}
.td-faq h2{{font-size:clamp(24px,3vw,36px);color:#2b2b2b;text-align:center;margin-bottom:48px}}
.td-faq details{{background:#fff;border:1px solid #e8e4de;border-radius:12px;margin-bottom:12px;overflow:hidden}}
.td-faq summary{{padding:20px 24px;font-size:clamp(16px,1.4vw,18px);font-weight:600;cursor:pointer;list-style:none;color:#2b2b2b}}
.td-faq summary::after{{content:"＋";float:right;transition:.3s}}
.td-faq details[open] summary::after{{content:"－"}}
.td-faq .td-faq-body{{padding:0 24px 20px;font-size:clamp(16px,1.4vw,18px);line-height:1.8;color:#5a5a5a}}
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


def _fallback_cta(product_name: str) -> str:
    return f"""<style>
.td-cta{{background:#3d6b4f;padding:80px 24px;text-align:center}}
.td-cta .td-container{{max-width:800px;margin:0 auto}}
.td-cta h2{{font-size:clamp(24px,3vw,36px);color:#fff;margin-bottom:16px}}
.td-cta p{{font-size:clamp(16px,1.5vw,19px);color:rgba(255,255,255,.85);line-height:1.8;margin-bottom:40px}}
.td-cta-note{{font-size:13px;color:rgba(255,255,255,.6);margin-top:24px}}
@media(max-width:767px){{.td-cta{{padding:56px 16px}}}}
</style>
<section class="td-cta">
  <div class="td-container">
    <h2>自分のペースで、はじめてみませんか</h2>
    <p>{product_name}は、特別な日のためだけでなく、毎日のルーティンにそっと寄り添うアイテムです。<br>まずは一度、ご自身で体感してみてください。</p>
    <p class="td-cta-note">発送は目立たない梱包でプライバシーに配慮しています。</p>
  </div>
</section>"""


class GeneratorEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_product_page(self, core: str, product_info: dict) -> str:
        info_text = "\n".join(f"- {k}: {v}" for k, v in product_info.items() if v)
        prompt = PRODUCT_PAGE_PROMPT.format(core=core, product_info=info_text)
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

    def generate_custom_liquid(self, core: str, product_info: dict) -> str:
        prompt = CUSTOM_LIQUID_PROMPT.format(
            core=core,
            product_name=product_info.get("name", ""),
            category=product_info.get("category", ""),
            price=product_info.get("price", ""),
            description=product_info.get("description", ""),
            features=product_info.get("features", ""),
            target=product_info.get("target", ""),
            use_scenes=product_info.get("use_scenes", ""),
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

    def generate_shopify_sections(self, core: str, product_info: dict) -> dict:
        product_name = product_info.get("name", "")
        # Truncate core to avoid 400 "prompt too long" errors from the API
        core_trimmed = core[:3500] if len(core) > 3500 else core
        args = dict(
            rules=_SHOPIFY_RULES,
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
            "shopify_common_css":               _fallback_css,
            "shopify_hero_section_code":        lambda: _fallback_hero(product_name),
            "shopify_about_section_code":       lambda: _fallback_about(product_name),
            "shopify_problem_section_code":     lambda: _fallback_problem(product_name),
            "shopify_features_section_code":    lambda: _fallback_features(product_name),
            "shopify_usage_scene_section_code": lambda: _fallback_scenes(product_name),
            "shopify_comparison_section_code":  lambda: _fallback_comparison(product_name),
            "shopify_faq_section_code":         lambda: _fallback_faq(product_name),
            "shopify_cta_section_code":         lambda: _fallback_cta(product_name),
        }
        sections = {}
        for key, marker, instructions in SHOPIFY_SECTION_CONFIGS:
            sections[key] = self._generate_one_section(
                key, marker, instructions, args, fallbacks[key]
            )
        return sections
