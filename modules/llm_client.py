import os
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """あなたはShopifyの商品ページ制作、広告制作、画像・動画生成プロンプト作成を専門とする
マーケティングAIアシスタントです。日本市場向けに特化し、自然な日本語で高品質なコンテンツを生成します。
ポルトガル語の入力も理解し、日本市場向けの自然な日本語に変換できます。
誇大表現、医療的断定表現、薬機法・景表法リスクのある表現は使用しません。"""


class LLMClient:
    def __init__(self):
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            api_key = os.getenv("ANTHROPIC_API_KEY", "")

        self.model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        if api_key:
            self._available = True
            self._client = Anthropic(api_key=api_key)
        else:
            self._available = False
            self._client = None

    @property
    def is_available(self) -> bool:
        return self._available

    def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        if not self._available:
            return "[APIキーが設定されていません。Streamlit Cloud の Settings > Secrets に ANTHROPIC_API_KEY を設定してください]"
        sys_prompt = system if system else SYSTEM_PROMPT
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=sys_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def generate_structured(self, prompt: str, system: str = "", max_tokens: int = 8192) -> str:
        return self.generate(prompt, system, max_tokens)
