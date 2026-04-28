from .llm_client import LLMClient

REFINE_PROMPT = """
あなたは日本語の表現を磨く専門家です。以下のテキストを指定されたモードで改善してください。

【モード】{mode}

【元のテキスト】
{text}

【各モードの指示】
- 自然な日本語：文法的に正確で、日本人が違和感なく読める表現にする
- 売れる日本語：購買意欲を高める表現にする（過度な誇張は避ける）
- 上品な日本語：高級感があり、品のある言い回しにする
- 女性向け：女性が共感しやすい温かみのある表現にする
- 男性向け：男性が受け入れやすいシンプルで信頼感のある表現にする
- 信頼感重視：専門性と誠実さが伝わる表現にする
- 柔らかい表現：堅苦しさをなくし、親しみやすくする
- 広告寄りの表現：広告コピーとして使えるキャッチーな表現にする
- 直訳感を消す：機械翻訳っぽさを取り除き、自然な日本語にする
- 誇張表現を弱める：過度な表現を現実的で信頼感のある表現に変える

重要な禁止事項（どのモードでも共通）：
- 「治る」「必ず効果がある」「確実に改善」「医学的に証明」などの断定表現はNG
- 法律リスクのある誇大表現はNG

【出力形式】
改善後：
（改善されたテキスト）

改善のポイント：
（どこをどう変えたか、簡潔に）
"""

CHECK_NATURALNESS_PROMPT = """
以下の日本語テキストの自然さをチェックしてください。

【テキスト】
{text}

【チェック項目】
1. 文法的に正しいか
2. 直訳っぽい表現がないか
3. 日本市場向けとして適切か
4. 誇張表現・断定表現がないか
5. 読みやすいか

【出力形式】
総合評価：〇〇点/100点

問題点：
（問題があれば箇条書きで）

修正案：
（修正が必要な部分と改善案）
"""


class JapaneseRefiner:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def refine(self, text: str, mode: str = "自然な日本語") -> str:
        prompt = REFINE_PROMPT.format(mode=mode, text=text)
        return self.llm.generate(prompt, max_tokens=4096)

    def check_naturalness(self, text: str) -> str:
        prompt = CHECK_NATURALNESS_PROMPT.format(text=text)
        return self.llm.generate(prompt, max_tokens=2048)
