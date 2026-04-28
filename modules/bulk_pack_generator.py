from .generator_engine import GeneratorEngine
from .llm_client import LLMClient

SHOPIFY_PACK_PROMPT = """
あなたはShopify商品ページ制作の専門家です。
以下のCoreから、Shopify出品に必要な全コンテンツを一括生成してください。

【Core】
{core}

【商品情報】
商品名: {product_name}
カテゴリ: {category}
価格: {price}

## 商品タイトル（メイン案 + 2案）

## キャッチコピー（5案）

## 商品説明文（Shopify用・HTML対応版）

## FAQ（7個・購入前不安を解消する内容重視）

## SEOタイトル

## メタディスクリプション（120文字以内）

## 商品タグ（15個、カンマ区切り）

## URLハンドル案（英語・小文字・ハイフン区切り）

## 画像Altテキスト（商品メイン・使用シーン・詳細の3つ）

## 注意事項
"""

BULK_PACK_PROMPTS = {
    "shopify": SHOPIFY_PACK_PROMPT,
}


class BulkPackGenerator:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.engine = GeneratorEngine(llm)

    def generate_shopify_pack(self, core: str, product_info: dict) -> dict:
        prompt = SHOPIFY_PACK_PROMPT.format(
            core=core,
            product_name=product_info.get("name", ""),
            category=product_info.get("category", ""),
            price=product_info.get("price", ""),
        )
        content = self.llm.generate_structured(prompt)
        return {"shopify_pack": content}

    def generate_ads_pack(self, core: str, product_info: dict) -> dict:
        product_name = product_info.get("name", "")
        ads = self.engine.generate_sns_content(core, product_name)
        video = self.engine.generate_video_scripts(core, product_name)
        return {"ads_content": ads, "video_scripts": video}

    def generate_sns_pack(self, core: str, product_info: dict) -> dict:
        product_name = product_info.get("name", "")
        return {"sns_content": self.engine.generate_sns_content(core, product_name)}

    def generate_image_pack(self, core: str, product_info: dict) -> dict:
        product_name = product_info.get("name", "")
        category = product_info.get("category", "")
        return {"image_prompts": self.engine.generate_image_prompts(core, product_name, category)}

    def generate_video_pack(self, core: str, product_info: dict) -> dict:
        product_name = product_info.get("name", "")
        return {"video_scripts": self.engine.generate_video_scripts(core, product_name)}

    def generate_full_pack(self, core: str, product_info: dict) -> dict:
        product_name = product_info.get("name", "")
        category = product_info.get("category", "")

        return {
            "product_page": self.engine.generate_product_page(core, product_info),
            "image_prompts": self.engine.generate_image_prompts(core, product_name, category),
            "video_scripts": self.engine.generate_video_scripts(core, product_name),
            "sns_content": self.engine.generate_sns_content(core, product_name),
        }
