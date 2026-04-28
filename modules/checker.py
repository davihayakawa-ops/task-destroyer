from .llm_client import LLMClient

CONSISTENCY_CHECK_PROMPT = """
以下のCoreと成果物が一致しているか確認してください。

【Core】
{core}

【チェック対象（{content_type}）】
{content}

【チェック項目】
1. メイン訴求が一致しているか
2. ターゲットが一致しているか
3. ブランドトーンが一致しているか
4. NG表現が使われていないか
5. 商品の強みが正しく反映されているか
6. 日本語は自然か
7. 断定表現・誇大表現がないか
8. CTAは適切か

【出力形式】
総合評価：〇〇点/100点

問題点：
（箇条書きで）

修正推奨箇所：
（具体的に）

薬機法・景表法リスクがある表現：
（あれば具体的に）
"""

RISK_CHECK_PROMPT = """
以下のテキストに薬機法・景表法・誇大広告のリスクがある表現がないか確認してください。

【テキスト】
{text}

【チェックする表現】
- 「治る」「治癒」「治療」
- 「必ず効果がある」「確実に」「絶対に」
- 「医学的に証明」「臨床的に証明」「科学的に証明」
- 「誰でも実感」「100%効果」
- 「病気に効く」「症状が消える」「完全に解決」
- その他、医療的断定表現、効能を断定する表現

【出力形式】
リスクレベル：低/中/高

検出された問題表現：
（箇条書きで：問題表現 → 理由 → 修正案）

総合コメント：
"""


class Checker:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def check_consistency(self, core: str, content: str, content_type: str) -> str:
        prompt = CONSISTENCY_CHECK_PROMPT.format(
            core=core, content=content, content_type=content_type
        )
        return self.llm.generate(prompt, max_tokens=2048)

    def check_risk_expressions(self, text: str) -> str:
        prompt = RISK_CHECK_PROMPT.format(text=text)
        return self.llm.generate(prompt, max_tokens=2048)
