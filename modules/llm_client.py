import os
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """あなたはShopifyの商品ページ制作、広告制作、画像・動画生成プロンプト作成を専門とする
マーケティングAIアシスタントです。日本市場向けに特化し、自然な日本語で高品質なコンテンツを生成します。
ポルトガル語の入力も理解し、日本市場向けの自然な日本語に変換できます。
誇大表現、医療的断定表現、薬機法・景表法リスクのある表現は使用しません。"""


def _read_api_key() -> Optional[str]:
    """
    st.secrets (Streamlit Cloud) を優先し、なければ os.getenv にフォールバック。
    @st.cache_resource でキャッシュされた LLMClient が secrets 未ロード状態で
    初期化された場合でも、generate() 呼び出し時に再取得できるよう独立関数にする。
    """
    try:
        import streamlit as st
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    key = os.getenv("ANTHROPIC_API_KEY", "")
    return key.strip() if key else None


class LLMClient:
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        self._client: Optional[Anthropic] = None
        self._try_init()

    def _try_init(self) -> bool:
        """キーが取得できればクライアントを初期化して True を返す。"""
        if self._client is not None:
            return True
        api_key = _read_api_key()
        if api_key:
            self._client = Anthropic(api_key=api_key)
            return True
        return False

    @property
    def is_available(self) -> bool:
        return self._try_init()

    def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        # @st.cache_resource でキャッシュ済みのインスタンスでも
        # ここで再試行することで secrets 遅延ロード問題を回避する
        if not self._try_init():
            return (
                "[APIキーが設定されていません。"
                "Streamlit Cloud の Settings > Secrets に ANTHROPIC_API_KEY を設定してください]"
            )
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
