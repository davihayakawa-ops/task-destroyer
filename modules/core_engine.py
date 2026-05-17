from .llm_client import LLMClient
from typing import Optional

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

【今回のCore生成方針】
{core_direction}

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

CORE_IMPROVEMENT_PROMPT = """
あなたはShopify商品販売のCoreを改善するプロマーケターです。
以下の既存Coreを、商品情報と改善方針に合わせて強化してください。

【商品情報】
{product_info}

【既存Core】
{core_text}

【改善方針】
{improvement_direction}

【改善ルール】
- 既存Coreの良い方向性は残す
- 抽象的な表現は、ターゲット・悩み・使用シーン・差別化が伝わる具体表現へ置き換える
- 薬機法・景表法リスクのある断定表現は弱める
- Custom Liquidの商品ページに展開しやすいよう、見出し・悩み・特徴・FAQ・CTAに使える材料を厚くする
- 出力形式は標準Coreフォーマットを維持し、各項目を「## 項目名」で出す
"""


class CoreEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_from_product(self, product_info: dict, core_options: Optional[dict] = None) -> str:
        info_text = "\n".join(
            f"- {k}: {v}" for k, v in product_info.items() if v
        )
        prompt = COMMERCE_CORE_PROMPT.format(
            product_info=info_text,
            core_direction=self._format_core_options(core_options),
        )
        return self.llm.generate_structured(prompt)

    def improve_core(self, core_text: str, product_info: dict, improvement_options: Optional[dict] = None) -> str:
        info_text = "\n".join(
            f"- {k}: {v}" for k, v in product_info.items() if v
        )
        prompt = CORE_IMPROVEMENT_PROMPT.format(
            product_info=info_text,
            core_text=core_text,
            improvement_direction=self._format_core_options(improvement_options),
        )
        return self.llm.generate_structured(prompt)

    def _format_core_options(self, options: Optional[dict] = None) -> str:
        options = options or {}
        strategy = options.get("strategy", "売れる訴求と安全性のバランス")
        safety = options.get("safety", "薬機法・景表法を安全寄り")
        focus = options.get("focus", [])
        tone = options.get("tone", "")
        focus_text = "、".join(focus) if isinstance(focus, list) else str(focus)
        return (
            f"- 生成方針: {strategy}\n"
            f"- 安全度: {safety}\n"
            f"- 重視する要素: {focus_text or '商品ページ化しやすさ、差別化、悩み共感'}\n"
            f"- 文章トーン: {tone or '日本市場向けに自然で信頼感のある表現'}"
        )

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
