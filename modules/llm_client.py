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
    def __init__(self, usage_limiter=None, audit_logger=None):
        self.usage_limiter = usage_limiter
        self.audit_logger = audit_logger
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
            if self.audit_logger:
                self.audit_logger.log("llm", "generate", "blocked", detail={"reason": "missing_api_key"})
            return "[APIキーが設定されていません。Streamlit Cloud の Settings > Secrets に ANTHROPIC_API_KEY を設定してください]"
        if self.usage_limiter:
            allowed, message = self.usage_limiter.try_consume()
            if not allowed:
                if self.audit_logger:
                    self.audit_logger.log("llm", "generate", "blocked", detail={"reason": "usage_limit"})
                return message
        sys_prompt = system if system else SYSTEM_PROMPT
        try:
            if self.audit_logger:
                self.audit_logger.log(
                    "llm", "generate", "started",
                    detail={"model": self.model, "max_tokens": max_tokens, "prompt_chars": len(prompt or "")},
                )
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=sys_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            if self.audit_logger:
                self.audit_logger.log(
                    "llm", "generate", "ok",
                    detail={"model": self.model, "output_chars": len(text or "")},
                )
            return text
        except anthropic.AuthenticationError:
            self._available = False
            if self.audit_logger:
                self.audit_logger.log("llm", "generate", "error", detail={"error_type": "authentication"})
            return "[APIキー認証エラー：Streamlit Cloud の Settings > Secrets で ANTHROPIC_API_KEY を確認してください]"
        except anthropic.RateLimitError:
            if self.audit_logger:
                self.audit_logger.log("llm", "generate", "error", detail={"error_type": "rate_limit"})
            return "[レート制限エラー：しばらく待ってから再試行してください]"
        except anthropic.APIError as e:
            if self.audit_logger:
                self.audit_logger.log("llm", "generate", "error", detail={"error_type": "api_error", "message": str(e)[:300]})
            return f"[Anthropic APIエラー：{e}]"

    def generate_structured(self, prompt: str, system: str = "", max_tokens: int = 8192) -> str:
        return self.generate(prompt, system, max_tokens)
