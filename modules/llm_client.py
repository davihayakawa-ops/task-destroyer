import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv

from modules.config import secret_or_env

load_dotenv()

SYSTEM_PROMPT = """あなたはShopifyの商品ページ制作、広告制作、画像・動画生成プロンプト作成を専門とする
マーケティングAIアシスタントです。日本語・ポルトガル語・英語の入力を理解し、指定された販売先市場と
出力言語に合わせて高品質なコンテンツを生成します。
日本市場では薬機法・景表法、米国市場ではFTC/FDA/広告プラットフォームの一般的な表現リスクに配慮し、
誇大表現、医療的断定表現、効果保証、根拠のないNo.1表現は使用しません。"""


class LLMClient:
    def __init__(self, usage_limiter=None):
        self.usage_limiter = usage_limiter
        api_key = secret_or_env("ANTHROPIC_API_KEY")

        self.model = secret_or_env("LLM_MODEL", "claude-sonnet-4-6")
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
        if self.usage_limiter:
            allowed, message = self.usage_limiter.try_consume()
            if not allowed:
                return message
        sys_prompt = system if system else SYSTEM_PROMPT
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=sys_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except anthropic.AuthenticationError:
            self._available = False
            return "[APIキー認証エラー：Streamlit Cloud の Settings > Secrets で ANTHROPIC_API_KEY を確認してください]"
        except anthropic.RateLimitError:
            return "[レート制限エラー：しばらく待ってから再試行してください]"
        except anthropic.APIError as e:
            return f"[Anthropic APIエラー：{e}]"

    def generate_structured(self, prompt: str, system: str = "", max_tokens: int = 8192) -> str:
        return self.generate(prompt, system, max_tokens)
