from .llm_client import LLMClient

IMPORT_PROMPT = """
あなたは外部で作成されたCoreやメモを、Task Destroyer標準フォーマットに変換する専門家です。

【外部から取り込まれたCore・メモ】
言語：{language}
作成元：{source}

{external_text}

【指示】
上記の外部Coreやメモを分析し、Task Destroyer標準フォーマットに変換してください。

変換の際の注意点：
1. 元のアイデアの良い部分を消さないこと
2. ポルトガル語の場合は意味を保ちながら日本市場向けの自然な日本語にすること
3. 直訳っぽい表現は避けること
4. 不足している項目はAIが補完し、「【AI補完】」と明記すること
5. 日本市場に合わせて誇張表現を弱め、信頼感のある表現にすること
6. 「治る」「必ず」「確実に」「医学的に証明」などはNG
7. 不明な部分は「【要確認】」と明記すること

【出力フォーマット】
以下の全項目を記述してください。情報が取れない場合は「【AI補完】内容」と記述してください。

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
## AI補完項目
## 人間が確認すべき項目
## 元Coreからの主な変更点・改善点
"""

PT_ACTIVATION_PROMPT = """
あなたはポルトガル語のCoreや商品メモを、日本市場向けの自然な日本語Coreに変換する専門家です。

【ポルトガル語Core/メモ】
{external_text}

【指示】
上記のポルトガル語Coreやメモの良い部分を活かしながら、日本市場で通用する自然なCoreに変換してください。

重視すること：
1. 元のアイデアを勝手に消さない
2. 良い表現や訴求を抽出する
3. 日本語として自然にする
4. 日本市場向けに整える
5. 直訳っぽさをなくす
6. 誇張表現を弱める
7. 信頼感・上品さを足す
8. 必要な項目が足りなければ補完案を出す（「【AI補完】」と明記）
9. 最終的に人間が編集できるように余白を残す

【出力】
まず「ポルトガル語Coreの良い点の分析」を記述し、
次に標準Coreフォーマットで出力してください。

## ポルトガル語Coreの良い点の分析

## 商品の一言コンセプト
（以下、全標準項目を出力）
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
## AI補完項目
## 人間が確認すべき項目
"""

LANG_DETECT_PROMPT = """
以下のテキストの言語を判定してください。
「日本語」「ポルトガル語」「英語」「混在」のいずれかで回答してください。
回答は1行のみ（例：「ポルトガル語」）。

テキスト：
{text}
"""


class CoreImporter:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def detect_language(self, text: str) -> str:
        prompt = LANG_DETECT_PROMPT.format(text=text[:500])
        result = self.llm.generate(prompt, max_tokens=20)
        return result.strip()

    def import_and_normalize(self, external_text: str, source: str = "不明", language: str = "自動判定") -> str:
        if language == "自動判定" or not language:
            language = self.detect_language(external_text)

        prompt = IMPORT_PROMPT.format(
            language=language,
            source=source,
            external_text=external_text
        )
        return self.llm.generate_structured(prompt)

    def activate_portuguese_core(self, external_text: str) -> str:
        prompt = PT_ACTIVATION_PROMPT.format(external_text=external_text)
        return self.llm.generate_structured(prompt)
