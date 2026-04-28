from modules.llm_client import LLMClient

CUSTOM_PROMPT = """
以下の自由入力をもとに、マーケティングCoreを生成してください。

【入力情報】
{user_input}

【生成内容】
入力内容をもとに、訴求の核となるCoreを作成してください。
ターゲット、訴求軸、ベネフィット、トーンを明確にしてください。
日本市場向けの自然な日本語で記述してください。
"""


class CustomCore:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(self, user_input: str) -> str:
        prompt = CUSTOM_PROMPT.format(user_input=user_input)
        return self.llm.generate_structured(prompt)
