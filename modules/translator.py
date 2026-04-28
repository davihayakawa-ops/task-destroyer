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
