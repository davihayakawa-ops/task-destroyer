import json
import re

from .llm_client import LLMClient

PT_TO_JA_PROMPT = """
あなたはポルトガル語（ブラジル）から日本語への翻訳の専門家です。
特にShopify商品ページ、広告文、マーケティングコンテンツの翻訳が得意です。

【ポルトガル語テキスト】
{text}

【指示】
上記を日本市場向けの自然な日本語に翻訳してください。

重要：
- 直訳ではなく、日本の消費者に自然に響く表現にすること
- 日本市場で商品ページや広告として使える言い回しにすること
- 誇張表現は弱め、信頼感のある表現にすること
- 上品さと親しみやすさのバランスをとること
- 「治る」「必ず」「確実に」などの断定表現は避けること

【出力形式】
翻訳：
（日本語訳）

※ 翻訳の補足（必要な場合のみ）：
（日本市場向けに変更した点など）
"""

JA_TO_PT_PROMPT = """
あなたは日本語からポルトガル語（ブラジル）への翻訳の専門家です。
特にShopify商品ページ、マーケティングコンテンツ、業務指示書の翻訳が得意です。

【日本語テキスト】
{text}

【指示】
上記をブラジルポルトガル語に翻訳してください。

重要：
- ブラジルポルトガル語を使うこと
- 業務用語はわかりやすい表現にすること
- 日本市場固有の表現は適切に説明を加えること

【出力形式】
Tradução:
（ポルトガル語訳）
"""

BILINGUAL_PROMPT = """
以下の日本語テキストを、日本語とポルトガル語（ブラジル）の二言語で表示してください。

【日本語テキスト】
{text}

【出力形式】
日本語：
{text}

Português:
（ポルトガル語訳）
"""


_FIELD_LABELS = {
    "name":                     "商品名",
    "description":              "商品説明",
    "price":                    "価格メモ",
    "category":                 "カテゴリ",
    "target":                   "ターゲット",
    "use_scenes":               "使用シーン",
    "notes":                    "商品メモ",
    "competitor_urls":          "競合URLメモ",
    "weaknesses":               "競合分析メモ",
    "features":                 "差別化ポイント",
    "age":                      "年齢層",
    "gender":                   "性別",
    "prohibited":               "禁止表現",
    "brand_tone":               "ブランドトーン",
}


class Translator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def pt_to_ja(self, text: str) -> str:
        prompt = PT_TO_JA_PROMPT.format(text=text)
        return self.llm.generate(prompt, max_tokens=4096)

    def ja_to_pt(self, text: str) -> str:
        prompt = JA_TO_PT_PROMPT.format(text=text)
        return self.llm.generate(prompt, max_tokens=4096)

    def bilingual(self, text: str) -> str:
        prompt = BILINGUAL_PROMPT.format(text=text)
        return self.llm.generate(prompt, max_tokens=4096)

    def translate_product_fields(self, fields: dict) -> dict:
        """Batch-translate product fields from pt-BR to ja in a single API call.

        Args:
            fields: {field_key: portuguese_text} — only non-empty values.
        Returns:
            {field_key: japanese_text}
        Raises:
            ValueError: if the API response cannot be parsed as JSON.
        """
        if not fields:
            return {}

        lines = []
        for key, value in fields.items():
            label = _FIELD_LABELS.get(key, key)
            lines.append(f"【{label} / {key}】\n{value}")
        fields_text = "\n\n".join(lines)

        json_template = "{\n" + ",\n".join(f'  "{k}": "..."' for k in fields) + "\n}"

        prompt = (
            "あなたはポルトガル語（ブラジル）→ 日本語の専門翻訳者です。\n"
            "以下のEC商品情報フィールドをすべて日本語に翻訳してください。\n\n"
            f"{fields_text}\n\n"
            "【翻訳ルール】\n"
            "- 日本の消費者に自然に響く表現にすること\n"
            "- URLや英数字の固有名詞はそのまま残すこと\n"
            "- 「治る」「必ず」「確実に」などの断定表現は避けること\n"
            "- 説明文・コードブロック不要\n\n"
            "以下のJSON形式のみで出力してください（キー名はそのまま、値を日本語訳に）:\n"
            f"{json_template}"
        )

        raw = self.llm.generate(prompt, max_tokens=4096)

        # Strip markdown code fences if present, then extract JSON object
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("翻訳レスポンスからJSONを取得できませんでした")

        result = json.loads(cleaned[start: end + 1])

        # Fallback: if a key is missing from the response, keep the original value
        for k in fields:
            if k not in result or not str(result[k]).strip():
                result[k] = fields[k]

        return result
