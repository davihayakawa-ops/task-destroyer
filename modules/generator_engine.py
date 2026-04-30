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


_SHOPIFY_RULES = """
【共通ルール】
- <html> <head> <body> タグは不要（Custom Liquidブロックに直接貼るため）
- JavaScriptは使わない / 外部CSS・外部ライブラリは使わない
- 全CSSクラス名には必ず「td-」プレフィックスを付ける
- @media (max-width: 767px) でスマホ対応
- 薬機法・景表法リスクのある表現は使わない（「治る」「必ず」「確実に」「医学的に証明」等）
- コードのみ出力。マークダウン(```)や説明文は不要

【フォントサイズ】大見出し:clamp(28px,4vw,48px) / セクション見出し:clamp(24px,3vw,36px) / 小見出し:clamp(18px,2vw,24px) / 本文:clamp(16px,1.4vw,18px);line-height:1.8

【レイアウト】max-width:1100px;margin:0 auto;padding:80px 24px → スマホ:padding:48px 16px

【デザイン】背景:#faf8f4 / テキスト:#2b2b2b / アクセント:#3d6b4f / カード:#fff;border:1px solid #e8e4de;border-radius:16px
各セクションは<style>タグを含む単体で動作するコードにする。
"""

SHOPIFY_SECTIONS_PROMPT_A = """
あなたはShopifyのカスタムLiquid制作の専門家です。
以下のCoreと商品情報をもとに、セクション別HTMLコード（00〜04）を生成してください。
{rules}
【Core】
{core}

【商品情報】
商品名:{product_name} / カテゴリ:{category} / 価格:{price}
説明:{description}
特徴:{features} / ターゲット:{target} / 使用シーン:{use_scenes}

マーカー形式で出力してください（マーカー行はそのまま出力すること）：

<<<SECTION_00_COMMON_CSS>>>
:root CSS変数（色・フォント・radius等）＋ .td-section / .td-container / .td-badge の基本クラス。<style>タグのみ。
<<<END_SECTION>>>

<<<SECTION_01_HERO>>>
ファーストビュー：カテゴリバッジ＋キャッチコピー(H1)＋サブコピー＋ベネフィット3点＋信頼バッジ。<style>＋<section>。
<<<END_SECTION>>>

<<<SECTION_02_ABOUT>>>
商品について：商品概要・誰のための商品か・使用シーン。<style>＋<section>。
<<<END_SECTION>>>

<<<SECTION_03_PROBLEM>>>
悩み・共感：ターゲットの悩みリスト＋なぜこの商品が解決策になるか。<style>＋<section>。
<<<END_SECTION>>>

<<<SECTION_04_FEATURES>>>
特徴カード：3〜5個のカード形式（絵文字＋見出し＋説明）。CSS Grid 3列→スマホ1列。<style>＋<section>。
<<<END_SECTION>>>
"""

SHOPIFY_SECTIONS_PROMPT_B = """
あなたはShopifyのカスタムLiquid制作の専門家です。
以下のCoreと商品情報をもとに、セクション別HTMLコード（05〜08）を生成してください。
{rules}
【Core】
{core}

【商品情報】
商品名:{product_name} / カテゴリ:{category} / 価格:{price}
説明:{description}
特徴:{features} / ターゲット:{target} / 使用シーン:{use_scenes}

マーカー形式で出力してください（マーカー行はそのまま出力すること）：

<<<SECTION_05_SCENES>>>
使用シーン：「自宅でのリラックスタイム」「夜の習慣に」「日常に組み込みやすい」「プライバシーを保ちながら続けたい方に」の視点で2〜4シーン。<style>＋<section>。
<<<END_SECTION>>>

<<<SECTION_06_COMPARISON>>>
比較表：「通院・薬に頼る場合」vs「この商品」で手軽さ・継続性・プライバシー・コストを比較。<table>形式。効果を断定しない表現。<style>＋<section>。
<<<END_SECTION>>>

<<<SECTION_07_FAQ>>>
FAQ（details/summary開閉式、5〜7項目）：
- 初めてでも使えますか？
- どのタイミングで使うのがおすすめですか？
- 周りに知られずに購入できますか？
- 継続しやすいですか？
- 使用前に確認することはありますか？
<style>＋<section>。
<<<END_SECTION>>>

<<<SECTION_08_CTA>>>
CTA：煽らず自然な購入後押し。「自分のペースで始められる」ニュアンス。安心感・プライバシー配慮を含む。<style>＋<section>。
<<<END_SECTION>>>
"""

SHOPIFY_SECTION_KEYS = [
    ("shopify_common_css",              "SECTION_00_COMMON_CSS"),
    ("shopify_hero_section_code",       "SECTION_01_HERO"),
    ("shopify_about_section_code",      "SECTION_02_ABOUT"),
    ("shopify_problem_section_code",    "SECTION_03_PROBLEM"),
    ("shopify_features_section_code",   "SECTION_04_FEATURES"),
    ("shopify_usage_scene_section_code","SECTION_05_SCENES"),
    ("shopify_comparison_section_code", "SECTION_06_COMPARISON"),
    ("shopify_faq_section_code",        "SECTION_07_FAQ"),
    ("shopify_cta_section_code",        "SECTION_08_CTA"),
]


def _parse_sections(raw: str, keys: list) -> dict:
    result = {}
    for store_key, marker in keys:
        m = re.search(rf"<<<{marker}>>>(.*?)<<<END_SECTION>>>", raw, re.DOTALL)
        result[store_key] = m.group(1).strip() if m else ""
    return result


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

    def generate_shopify_sections(self, core: str, product_info: dict) -> dict:
        args = dict(
            rules=_SHOPIFY_RULES,
            core=core,
            product_name=product_info.get("name", ""),
            category=product_info.get("category", ""),
            price=product_info.get("price", ""),
            description=product_info.get("description", ""),
            features=product_info.get("features", ""),
            target=product_info.get("target", ""),
            use_scenes=product_info.get("use_scenes", ""),
        )
        keys_a = SHOPIFY_SECTION_KEYS[:5]   # 00–04
        keys_b = SHOPIFY_SECTION_KEYS[5:]   # 05–08

        raw_a = self.llm.generate_structured(
            SHOPIFY_SECTIONS_PROMPT_A.format(**args), max_tokens=8192
        )
        raw_b = self.llm.generate_structured(
            SHOPIFY_SECTIONS_PROMPT_B.format(**args), max_tokens=8192
        )

        sections = {**_parse_sections(raw_a, keys_a), **_parse_sections(raw_b, keys_b)}
        sections["_raw_a"] = raw_a
        sections["_raw_b"] = raw_b

        product_name = product_info.get("name", "")
        if not sections.get("shopify_usage_scene_section_code"):
            sections["shopify_usage_scene_section_code"] = _fallback_scenes(product_name)
        if not sections.get("shopify_comparison_section_code"):
            sections["shopify_comparison_section_code"] = _fallback_comparison(product_name)
        if not sections.get("shopify_faq_section_code"):
            sections["shopify_faq_section_code"] = _fallback_faq(product_name)
        if not sections.get("shopify_cta_section_code"):
            sections["shopify_cta_section_code"] = _fallback_cta(product_name)

        return sections
