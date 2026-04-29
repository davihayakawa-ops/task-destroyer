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
