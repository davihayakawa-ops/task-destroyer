from .llm_client import LLMClient

CORE_FIELDS = [
    "concept", "main_target", "sub_target", "customer_pain", "customer_ideal",
    "pre_purchase_anxiety", "purchase_barrier", "unique_value", "usp",
    "main_appeal", "sub_appeal", "benefits", "reassurance", "differentiation",
    "brand_tone", "visual_tone", "copywriting_policy", "recommended_expressions",
    "prohibited_expressions", "ng_words", "appeal_priority",
    "product_page_emphasis", "image_show", "video_show", "cta_policy",
    "japanese_rules", "pt_explanation", "ai_completed", "human_check",
]

COMMERCE_CORE_PROMPT = """
あなたはShopify商品販売のプロマーケターです。以下の商品情報から、商品の「Core（核）」を生成してください。

Coreとは、この商品を売るためのマーケティングの核心です。
商品ページ、広告文、画像プロンプト、動画台本、SNS投稿など全ての成果物は、このCoreをベースに生成されます。

【商品情報】
{product_info}

【生成するCore項目】
以下の項目を、日本市場向けの自然な日本語で、できるだけ具体的に記述してください。
各項目は「## 項目名」の形式で記述し、内容を箇条書きまたは文章で書いてください。

## 商品の一言コンセプト
## メインターゲット
## サブターゲット
## 顧客の悩み
## 顧客の理想
## 購入前の不安
## 購入障壁
## 商品の独自価値
## USP（独自の強み）
## メイン訴求
## サブ訴求
## ベネフィット
## 安心材料
## 競合との差別化
## ブランドトーン
## ビジュアルトーン
## コピーライティング方針
## 推奨表現
## 禁止表現
## NGワード
## 訴求優先順位
## 商品ページで強調すべきこと
## 画像で見せるべきこと
## 動画で見せるべきこと
## CTA方針
## 日本語表現ルール
## ポルトガル語ユーザー向け説明
## AI補完項目（不確かな部分があればここに記載）
## 人間が確認すべき項目

重要な注意点：
- 「治る」「必ず効果がある」「確実に改善」「医学的に証明」などの断定・誇大表現は使わないこと
- 日本市場向けの自然で上品な日本語を使うこと
- 直訳っぽい表現は避けること
- 商品の強みを活かした訴求にすること
"""


class CoreEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_from_product(self, product_info: dict) -> str:
        info_text = "\n".join(
            f"- {k}: {v}" for k, v in product_info.items() if v
        )
        prompt = COMMERCE_CORE_PROMPT.format(product_info=info_text)
        return self.llm.generate_structured(prompt)

    def parse_core_sections(self, core_text: str) -> dict:
        """Parse ## section headers into a dict."""
        sections = {}
        current_key = None
        current_lines = []

        for line in core_text.splitlines():
            if line.startswith("## "):
                if current_key:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = line[3:].strip()
                current_lines = []
            else:
                if current_key:
                    current_lines.append(line)

        if current_key:
            sections[current_key] = "\n".join(current_lines).strip()

        return sections
