import html
import re

import streamlit as st

from .generated_content import combine_generated_items
from .selection_config import (
    AS_MEDIA,
    AS_PRESETS,
    AS_TYPES,
    IP_ITEMS,
    IP_PRESETS,
    VS_COMBO_PRESETS,
    VS_DURATIONS,
    VS_ITEMS,
    VS_PRESETS,
    VS_TYPES,
)


_GEN_CSS = """
<style>
.gen-hero{background:#111827;border:1px solid #263244;border-radius:10px;padding:16px 18px;margin:0 0 16px}
.gen-hero h3{color:#f8fafc;font-size:1rem;font-weight:850;margin:0 0 6px}
.gen-hero p{color:#a8b3c7;font-size:.82rem;line-height:1.65;margin:0}
.gen-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0 0 16px}
.gen-card{background:#111827;border:1px solid #263244;border-radius:8px;padding:13px 14px;min-height:88px}
.gen-card strong{display:block;color:#f8fafc;font-size:.84rem;margin-bottom:5px}
.gen-card span{display:block;color:#94a3b8;font-size:.74rem;line-height:1.55}
.gen-plan{background:#0b1220;border:1px solid #334155;border-radius:8px;padding:12px 14px;margin:12px 0;color:#cbd5e1;font-size:.8rem}
.gen-plan strong{color:#f8fafc}
.gen-pill{display:inline-block;background:rgba(59,130,246,.14);border:1px solid #2563eb;color:#bfdbfe;border-radius:999px;padding:4px 10px;margin:4px 6px 4px 0;font-size:.72rem;font-weight:700}
.gen-result-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:8px}
.gen-result-title{color:#f8fafc;font-weight:850;font-size:.96rem}
.gen-result-meta{color:#94a3b8;font-size:.72rem;line-height:1.5}
.gen-copy-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:8px 0 12px}
.gen-copy-card{background:#0b1220;border:1px solid #263244;border-radius:8px;padding:10px 12px}
.gen-copy-card strong{display:block;color:#f8fafc;font-size:.78rem;margin-bottom:4px}
.gen-copy-card span{display:block;color:#94a3b8;font-size:.68rem;line-height:1.45}
.gen-check-box{background:#0b1220;border:1px solid #263244;border-radius:8px;padding:12px 14px;margin:10px 0;color:#cbd5e1;font-size:.82rem;line-height:1.7;white-space:pre-wrap}
@media(max-width:900px){.gen-grid{grid-template-columns:1fr}}
@media(max-width:900px){.gen-copy-grid{grid-template-columns:1fr}}
</style>
"""


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _hero(title: str, body: str) -> str:
    return f'<div class="gen-hero"><h3>{_esc(title)}</h3><p>{_esc(body)}</p></div>'


def _info_grid(cards):
    return (
        '<div class="gen-grid">'
        + "".join(
            f'<div class="gen-card"><strong>{_esc(title)}</strong><span>{_esc(body)}</span></div>'
            for title, body in cards
        )
        + "</div>"
    )


def _generation_market_options() -> dict:
    return {
        "target_market": st.session_state.get("generation_target_market", "japan"),
        "output_language": st.session_state.get("generation_output_language", "ja"),
        "market_note": st.session_state.get("generation_market_note", ""),
    }


_US_MARKET_PRESETS = [
    (
        "us_dtc",
        "US DTC",
        "米国DTCブランド風。短い見出し、ベネフィット先行、レビュー/FAQで不安解消、FTC-safeで自然な英語。",
    ),
    (
        "amazon",
        "Amazon",
        "Amazon商品ページ風。検索意図、機能ベネフィット、比較しやすい箇条書き、レビュー前提の信頼材料を強める。",
    ),
    (
        "meta_ads",
        "Meta Ads",
        "Meta広告向け。冒頭フック、悩み共感、短いCTA、広告審査に安全な表現、スクロール停止コピーを重視。",
    ),
    (
        "tiktok_shop",
        "TikTok Shop",
        "TikTok Shop向け。UGC風、速いテンポ、実演・使用感・短いフック、買いやすいCTAを重視。",
    ),
    (
        "premium_us",
        "Premium US",
        "米国プレミアムブランド風。過度に煽らず、上質感・余白・信頼・簡潔なコピー・落ち着いたCTAを重視。",
    ),
]


def _apply_market_preset(note: str, target_market: str = "us", output_language: str = "en"):
    st.session_state["generation_target_market"] = target_market
    st.session_state["generation_output_language"] = output_language
    st.session_state["generation_market_note"] = note


def _ui(ja: str, pt: str, en: str) -> str:
    lang = st.session_state.get("lang", "ja")
    if lang == "ja":
        return ja
    if lang == "en":
        return en
    return pt


IP_LABEL_EN = {
    "main_visual": "🖼️ Product page main visual",
    "product_only": "📦 Product-only image",
    "usage_scene": "🌿 Usage scene image",
    "benefit": "✨ Benefit visual",
    "comparison": "⚖️ Comparison image",
    "ad_banner": "📢 Ad banner image",
    "sns_post": "📱 Social post image",
    "story": "📖 Story image",
}
IP_PRESET_EN = {
    "shopify": "🛒 Shopify page set",
    "sns": "📱 Social asset set",
    "ads": "📢 Ad operation set",
    "full": "⚡ Full generation",
    "custom": "✏️ Custom",
}
VS_TYPE_EN = {
    "tiktok": "🎵 TikTok script",
    "reels": "📸 Instagram Reels script",
    "yt_shorts": "▶️ YouTube Shorts script",
    "ad_script": "📢 Ad script",
    "narration": "🎤 Voiceover narration",
    "timeline": "📋 Timeline by seconds",
    "shooting": "🎬 Script with shooting direction",
    "higgs_marketing_studio": "🧪 Higgs Marketing Studio prompt",
}
VS_PRESET_EN = {
    "sns": "📱 Social post set",
    "ads": "📢 Ad operation set",
    "shorts": "▶️ Shorts production set",
    "full": "⚡ Full generation",
    "custom": "✏️ Custom",
}
AS_TYPE_EN = {
    "post": "Post copy",
    "ad_copy": "Ad copy",
    "caption": "Caption",
    "hashtag": "Hashtags",
    "cta": "CTA",
    "hook": "Short hook",
    "comment_bait": "Comment prompt",
}
AS_PRESET_EN = {
    "sns": "📱 Social post set",
    "ads": "📢 Ad operation set",
    "custom": "✏️ Custom",
}


def _label_by_lang(key: str, ja: str, pt: str, en_map: dict[str, str]) -> str:
    lang = st.session_state.get("lang", "ja")
    if lang == "ja":
        return ja
    if lang == "en":
        return en_map.get(key, ja)
    return pt


def _render_quality_controls(prefix: str, is_ja: bool, page_kind: str) -> dict:
    lang = st.session_state.get("lang", "ja")
    st.markdown("### " + _ui("生成の方向性", "Direção da geração", "Generation direction"))
    if page_kind == "image":
        purpose_opts = ["Shopify商品ページ", "広告バナー", "SNS投稿", "Higgsfield/画像AI用", "高級ブランド風"]
        purpose_pt = ["Página Shopify", "Banner de anúncio", "Post SNS", "Para Higgsfield/IA de imagem", "Marca premium"]
        purpose_en = ["Shopify product page", "Ad banner", "Social post", "For Higgsfield / image AI", "Premium brand style"]
    elif page_kind == "video":
        purpose_opts = ["TikTok/Reels", "YouTube Shorts", "広告動画", "Higgs Marketing Studio用", "撮影指示用"]
        purpose_pt = ["TikTok/Reels", "YouTube Shorts", "Vídeo de anúncio", "Para Higgs Marketing Studio", "Direção de filmagem"]
        purpose_en = ["TikTok / Reels", "YouTube Shorts", "Ad video", "For Higgs Marketing Studio", "Shooting direction"]
    else:
        purpose_opts = ["通常投稿", "広告運用", "商品ページ誘導", "キャンペーン", "コメント獲得"]
        purpose_pt = ["Post normal", "Anúncio pago", "Levar à página do produto", "Campanha", "Gerar comentários"]
        purpose_en = ["Organic post", "Paid ad", "Drive to product page", "Campaign", "Get comments"]
    tone_opts = ["上品・信頼感", "ナチュラル", "高級感", "悩み共感", "SNS広告・強め", "ミニマル"]
    tone_pt = ["Elegante/confiável", "Natural", "Premium", "Empatia com dor", "Anúncio SNS forte", "Minimalista"]
    tone_en = ["Elegant / trustworthy", "Natural", "Premium", "Pain empathy", "Stronger social ad style", "Minimal"]
    strength_opts = ["控えめ", "標準", "強め"]
    strength_pt = ["Suave", "Padrão", "Forte"]
    strength_en = ["Soft", "Standard", "Strong"]
    purpose_display = purpose_opts if lang == "ja" else (purpose_en if lang == "en" else purpose_pt)
    tone_display = tone_opts if lang == "ja" else (tone_en if lang == "en" else tone_pt)
    strength_display = strength_opts if lang == "ja" else (strength_en if lang == "en" else strength_pt)

    col1, col2, col3 = st.columns(3)
    with col1:
        purpose = st.selectbox(
            _ui("用途", "Uso", "Use case"),
            purpose_display,
            key=f"{prefix}_purpose",
        )
    with col2:
        tone = st.selectbox(
            _ui("雰囲気", "Tom", "Tone"),
            tone_display,
            key=f"{prefix}_tone",
        )
    with col3:
        strength = st.selectbox(
            _ui("訴求の強さ", "Força", "Persuasion strength"),
            strength_display,
            index=1,
            key=f"{prefix}_strength",
        )
    note = st.text_input(
        _ui("追加指示（任意）", "Instrução extra (opcional)", "Extra instruction (optional)"),
        placeholder=_ui("例：黒背景、高級感、30代女性向け", "Ex.: fundo escuro, premium, mulheres 30+", "Example: dark background, premium, women 30+"),
        key=f"{prefix}_note",
    )
    st.markdown("### " + _ui("販売先・出力言語", "Mercado e idioma de saída", "Market and output language"))
    st.markdown("**" + _ui("米国向けプリセット", "Presets para EUA", "US presets") + "**")
    preset_cols = st.columns(len(_US_MARKET_PRESETS))
    for i, (preset_key, label, preset_note) in enumerate(_US_MARKET_PRESETS):
        with preset_cols[i]:
            if st.button(label, key=f"{prefix}_market_preset_{preset_key}", use_container_width=True):
                _apply_market_preset(preset_note)
                st.rerun()

    market_col1, market_col2 = st.columns(2)
    market_labels = {
        "japan": _ui("日本向け", "Japão", "Japan"),
        "us": _ui("米国向け", "Estados Unidos", "United States"),
        "global": _ui("グローバル", "Global", "Global"),
    }
    language_labels = {
        "ja": _ui("日本語", "Japonês", "Japanese"),
        "en": _ui("英語", "Inglês", "English"),
        "pt": _ui("ポルトガル語", "Português", "Portuguese"),
    }
    with market_col1:
        target_market = st.selectbox(
            _ui("販売先", "Mercado", "Target market"),
            ["japan", "us", "global"],
            key="generation_target_market",
            format_func=lambda v: market_labels.get(v, v),
        )
    with market_col2:
        output_language = st.selectbox(
            _ui("生成する言語", "Idioma gerado", "Output language"),
            ["ja", "en", "pt"],
            key="generation_output_language",
            format_func=lambda v: language_labels.get(v, v),
        )
    market_note = st.text_input(
        _ui("米国向けの追加指定（任意）", "Instrução de mercado (opcional)", "Market instruction (optional)"),
        placeholder=_ui(
            "例: 米国DTCブランド風、FTCに安全、短いCTA、価格はUSD前提",
            "Ex.: estilo DTC dos EUA, seguro para FTC, CTA curto, preço em USD",
            "Example: US DTC brand style, FTC-safe, short CTA, USD pricing",
        ),
        key="generation_market_note",
    )
    return {
        "purpose": purpose,
        "tone": tone,
        "strength": strength,
        "note": note,
        "target_market": target_market,
        "output_language": output_language,
        "market_note": market_note,
    }


def _render_plan(selected_labels, quality: dict, is_ja: bool):
    lang = st.session_state.get("lang", "ja")
    if not selected_labels:
        msg = _ui("まだ生成対象が選ばれていません。", "Nenhum item selecionado ainda.", "No generation targets selected yet.")
        st.markdown(f'<div class="gen-plan">{_esc(msg)}</div>', unsafe_allow_html=True)
        return
    title = _ui("生成予定", "Será gerado", "Will be generated")
    settings = (
        f"{_ui('用途', 'Uso', 'Use case')}: {quality.get('purpose', '-')}"
        f" / {_ui('雰囲気', 'Tom', 'Tone')}: {quality.get('tone', '-')}"
        f" / {_ui('強さ', 'Força', 'Strength')}: {quality.get('strength', '-')}"
    )
    pills = "".join(f'<span class="gen-pill">{_esc(label)}</span>' for label in selected_labels)
    st.markdown(
        f'<div class="gen-plan"><strong>{_esc(title)}: {len(selected_labels)}</strong><br>'
        f'{_esc(settings)}<br>{pills}</div>',
        unsafe_allow_html=True,
    )


def _set_video_selection(durations, types):
    for key, _, _ in VS_DURATIONS:
        st.session_state[f"chk_vs_duration_{key}"] = key in durations
    for key, _, _ in VS_TYPES:
        st.session_state[f"chk_vs_type_{key}"] = key in types


def _render_video_goal_cards(is_ja: bool):
    lang = st.session_state.get("lang", "ja")
    goals = [
        (
            "sns_start",
            _ui("迷ったらこれ", "Recomendado", "Recommended"),
            _ui("まずSNS動画を作る", "Criar vídeo SNS", "Create a social video"),
            "15秒・30秒 / TikTok・Reels・ナレーション。最初の広告テストや投稿に使いやすいセット。"
            if is_ja else (
                "15s and 30s / TikTok, Reels, and narration. Good for a first test ad or post."
                if lang == "en" else
                "15s e 30s / TikTok, Reels e narração. Bom para primeiro teste ou post."
            ),
            ["15s", "30s"],
            ["tiktok", "reels", "narration"],
        ),
        (
            "higgs_video",
            _ui("動画AI用", "Para IA", "For video AI"),
            _ui("Higgsで動画生成", "Gerar no Higgs", "Generate with Higgs"),
            "30秒 / Higgs用プロンプト・秒数別構成・撮影指示。Higgsfieldに貼る素材を作ります。"
            if is_ja else (
                "30s / Higgs prompt, timeline, and shooting direction. Creates material to paste into Higgsfield."
                if lang == "en" else
                "30s / prompt Higgs, cronograma e direção. Cria material para colar no Higgsfield."
            ),
            ["30s"],
            ["higgs_marketing_studio", "timeline", "shooting"],
        ),
        (
            "ad_test",
            _ui("広告向け", "Anúncio", "For ads"),
            _ui("広告素材を作る", "Criar material de anúncio", "Create ad assets"),
            "30秒・45秒 / 広告台本・撮影指示・秒数別構成。不安解消とCTAを強めます。"
            if is_ja else (
                "30s and 45s / ad script, shooting direction, and timeline. Strengthens objection handling and CTA."
                if lang == "en" else
                "30s e 45s / roteiro de anúncio, direção e cronograma. Reforça objeções e CTA."
            ),
            ["30s", "45s"],
            ["ad_script", "shooting", "timeline"],
        ),
        (
            "shorts_one",
            _ui("YouTube用", "YouTube", "For YouTube"),
            _ui("Shortsを作る", "Criar Shorts", "Create Shorts"),
            "30秒・60秒 / Shorts台本・秒数別構成・Higgs用。説明型の短尺動画に向いています。"
            if is_ja else (
                "30s and 60s / Shorts script, timeline, and Higgs prompt. Good for short explanatory videos."
                if lang == "en" else
                "30s e 60s / Shorts, cronograma e Higgs. Bom para vídeos explicativos curtos."
            ),
            ["30s", "60s"],
            ["yt_shorts", "timeline", "higgs_marketing_studio"],
        ),
    ]
    st.markdown("### " + _ui("1. 目的から選ぶ", "1. Escolha pelo objetivo", "1. Choose by goal"))
    st.markdown('<div class="cs-info">💡 ' + (
        "何を選べばいいか分からない場合は、左上の「まずSNS動画を作る」を押してください。必要な秒数と内容が自動で選ばれます。"
        if is_ja else (
            "If you are not sure what to choose, click the recommended option. The duration and contents will be selected automatically."
            if lang == "en" else
            "Se não souber o que escolher, clique no recomendado. A duração e os conteúdos serão selecionados automaticamente."
        )
    ) + '</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (goal_id, tag, title, body, durations, types) in enumerate(goals):
        with cols[i % 2]:
            st.markdown(
                f'<div class="gen-card"><strong>{_esc(tag)} / {_esc(title)}</strong>'
                f'<span>{_esc(body)}</span></div>',
                unsafe_allow_html=True,
            )
            if st.button(_ui("この目的でセット", "Usar este objetivo", "Use this goal"),
                         key=f"vs_goal_{goal_id}", use_container_width=True,
                         type="primary" if i == 0 else "secondary"):
                _set_video_selection(durations, types)
                st.rerun()


def _item_meta(category: str, key: str, is_ja: bool) -> str:
    lang = st.session_state.get("lang", "ja")
    ip = {
        "main_visual": ("Shopifyの最初に置くメイン画像 / 16:9・4:5", "Imagem principal para Shopify / 16:9 ou 4:5"),
        "product_only": ("商品単体を正確に見せる / 1:1", "Mostrar o produto com clareza / 1:1"),
        "usage_scene": ("使っている場面を見せる / 4:5", "Cena de uso / 4:5"),
        "benefit": ("ベネフィットを視覚化 / 4:5", "Visualizar benefício / 4:5"),
        "comparison": ("違いを分かりやすく見せる / 16:9", "Mostrar diferenciais / 16:9"),
        "ad_banner": ("広告・LP上部向け / 16:9", "Para anúncio ou topo de LP / 16:9"),
        "sns_post": ("Instagram投稿向け / 1:1・4:5", "Para Instagram / 1:1 ou 4:5"),
        "story": ("縦型ストーリー向け / 9:16", "Stories vertical / 9:16"),
    }
    vs = {
        "tiktok": ("テンポ重視。冒頭3秒のフックを強めます。", "Ritmo rápido e gancho forte nos 3 primeiros segundos."),
        "reels": ("見た目と保存したくなる整理を重視します。", "Foco visual e conteúdo salvável."),
        "yt_shorts": ("短尺で理解しやすい教育・比較型にします。", "Formato educativo/comparativo curto."),
        "ad_script": ("広告配信向けに不安解消とCTAを強めます。", "Para anúncio pago, com CTA e redução de objeções."),
        "narration": ("読み上げやすい音声本文を作ります。", "Texto natural para narração."),
        "timeline": ("秒数ごとの映像・テロップ・音声を表にします。", "Tabela por tempo com vídeo, texto e áudio."),
        "shooting": ("カメラ・照明・小物まで指示します。", "Direção de câmera, luz e objetos."),
        "higgs_marketing_studio": ("Higgsに貼る英語プロンプトを作ります。", "Prompt em inglês para colar no Higgs."),
    }
    ads = {
        "post": ("通常投稿向けの本文を複数案で作ります。", "Variações para post normal."),
        "ad_copy": ("広告配信用の短い訴求を作ります。", "Copy curta para anúncio pago."),
        "caption": ("投稿の説明文として使いやすく整えます。", "Legenda pronta para postagem."),
        "hashtag": ("使いやすいタグを用途別に出します。", "Hashtags por uso."),
        "cta": ("クリック・保存・購入への導線を作ります。", "Chamadas para ação."),
        "hook": ("冒頭で止める短いフックを作ります。", "Ganchos curtos de atenção."),
        "comment_bait": ("自然なコメント誘導を作ります。", "Indução natural de comentários."),
    }
    data = {"ip": ip, "vs": vs, "ads": ads}.get(category, {})
    en = {
        "ip": {
            "main_visual": "Main Shopify image / 16:9 or 4:5",
            "product_only": "Show the product clearly / 1:1",
            "usage_scene": "Usage scene / 4:5",
            "benefit": "Visualize the benefit / 4:5",
            "comparison": "Show differences clearly / 16:9",
            "ad_banner": "For ads or top of LP / 16:9",
            "sns_post": "For Instagram / 1:1 or 4:5",
            "story": "Vertical story / 9:16",
        },
        "vs": {
            "tiktok": "Fast rhythm and a strong first 3-second hook.",
            "reels": "Focus on visuals and save-worthy organization.",
            "yt_shorts": "Short educational/comparison format.",
            "ad_script": "For paid ads, with CTA and objection handling.",
            "narration": "Natural text for voiceover.",
            "timeline": "Table by time with visual, text, and audio.",
            "shooting": "Camera, lighting, and prop direction.",
            "higgs_marketing_studio": "English prompt to paste into Higgs.",
        },
        "ads": {
            "post": "Multiple variations for organic posts.",
            "ad_copy": "Short copy for paid ads.",
            "caption": "Ready-to-use post caption.",
            "hashtag": "Hashtags by use case.",
            "cta": "Calls to action for clicks, saves, and purchases.",
            "hook": "Short attention-stopping hooks.",
            "comment_bait": "Natural comment prompts.",
        },
    }.get(category, {})
    ja, pt = data.get(key, ("", ""))
    if lang == "en":
        return en.get(key, ja)
    return ja if is_ja else pt


def _extract_markdown_section(content: str, heading: str) -> str:
    pattern = rf"(?ms)^##+\s*{re.escape(heading)}\s*\n(.*?)(?=^##+\s+|\Z)"
    match = re.search(pattern, content or "")
    if match:
        return match.group(1).strip()
    alt_pattern = rf"(?ms)^[-*]\s*{re.escape(heading)}\s*:\s*(.*?)(?=^[-*]\s+[\w /-]+:|\Z)"
    alt_match = re.search(alt_pattern, content or "")
    if alt_match:
        return alt_match.group(1).strip()
    return ""


def _copy_sections(category_key: str, item_key: str, content: str, is_ja: bool):
    lang = st.session_state.get("lang", "ja")
    if category_key == "image_prompts":
        return [
            (_ui("生成AIプロンプト（英語）", "Prompt em inglês", "Image AI prompt (English)"), _extract_markdown_section(content, "生成AIプロンプト（英語）")),
            (_ui("日本語メモ", "Notas", "Notes"), _extract_markdown_section(content, "日本語メモ（制作担当者への補足）") or _extract_markdown_section(content, "日本語メモ")),
            (_ui("NG要素", "Itens proibidos", "Avoid"), _extract_markdown_section(content, "NG要素")),
            (_ui("入れると良いテキスト", "Texto recomendado", "Recommended text"), _extract_markdown_section(content, "入れると良いテキスト")),
        ]
    if category_key == "video_scripts":
        if "higgs_marketing_studio" in item_key:
            return [
                (_ui("Higgs用プロンプト", "Prompt Higgs", "Higgs prompt"), _extract_markdown_section(content, "Higgs Marketing Studio Prompt") or content),
                (_ui("Scene direction", "Direção de cenas", "Scene direction"), _extract_markdown_section(content, "Scene-by-scene Direction")),
                ("Voiceover" if is_ja else "Voiceover", _extract_markdown_section(content, "Voiceover Script")),
                (_ui("日本語メモ", "Notas", "Notes"), _extract_markdown_section(content, "日本語メモ")),
            ]
        return [
            (_ui("冒頭3秒フック", "Gancho inicial", "Opening 3-second hook"), _extract_markdown_section(content, "冒頭3秒フック")),
            (_ui("完成台本", "Roteiro completo", "Complete script"), _extract_markdown_section(content, "完成台本")),
            (_ui("ナレーション", "Narração", "Narration"), _extract_markdown_section(content, "ナレーション")),
            (_ui("テロップ", "Legendas", "On-screen captions"), _extract_markdown_section(content, "テロップ")),
            (_ui("映像・撮影指示", "Direção visual", "Visual / shooting direction"), _extract_markdown_section(content, "映像・撮影指示")),
            (_ui("CTA案", "CTAs", "CTA ideas"), _extract_markdown_section(content, "CTA案 3つ") or _extract_markdown_section(content, "CTA案")),
        ]
    if category_key == "ads_sns_items":
        return [
            (_ui("案1", "Opção 1", "Option 1"), _extract_markdown_section(content, "案1")),
            (_ui("案2", "Opção 2", "Option 2"), _extract_markdown_section(content, "案2")),
            (_ui("案3", "Opção 3", "Option 3"), _extract_markdown_section(content, "案3")),
            (_ui("短縮版", "Versão curta", "Short version"), _extract_markdown_section(content, "短縮版")),
            ("CTA" if is_ja else "CTA", _extract_markdown_section(content, "CTA")),
            (_ui("注意点", "Cuidados", "Notes"), _extract_markdown_section(content, "注意点")),
        ]
    return []


def _render_copy_parts(category_key: str, item_key: str, content: str, is_ja: bool):
    sections = [(label, text) for label, text in _copy_sections(category_key, item_key, content, is_ja) if text]
    if not sections:
        st.markdown('<div class="cs-info">💡 ' + (
            "分割できる項目が見つかりませんでした。全文タブから確認してください。"
            if is_ja else
            "Nenhuma seção separável encontrada. Confira na aba de texto completo."
        ) + '</div>', unsafe_allow_html=True)
        return
    st.markdown(
        '<div class="gen-copy-grid">'
        + "".join(
            f'<div class="gen-copy-card"><strong>{_esc(label)}</strong>'
            f'<span>{_esc(str(len(text)))} {"文字" if is_ja else "caracteres"}</span></div>'
            for label, text in sections
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    labels = [label for label, _ in sections]
    selected_label = st.selectbox(
        "コピーする部分" if is_ja else "Parte para copiar",
        labels,
        key=f"copy_part_{category_key}_{item_key}",
    )
    selected_text = next(text for label, text in sections if label == selected_label)
    st.text_area(
        "コピー用テキスト" if is_ja else "Texto para copiar",
        value=selected_text,
        height=180,
        key=f"copy_text_{category_key}_{item_key}_{selected_label}",
    )
    safe_fname = item_key.replace("::", "_").replace("/", "_")
    st.download_button(
        "⬇️ " + _ui("この部分をダウンロード", "Baixar esta parte", "Download this part"),
        data=selected_text.encode("utf-8"),
        file_name=f"{safe_fname}_{selected_label}.txt",
        mime="text/plain",
        key=f"dl_part_{category_key}_{item_key}_{selected_label}",
        use_container_width=True,
    )


def _load_category_state(svc: dict, category_key: str):
    """Load per-item results from storage if not already in session_state."""
    if category_key in st.session_state:
        st.session_state.setdefault(f"{category_key}_checks", {})
        return
    pid = st.session_state.get("product_id", "")
    if pid:
        try:
            saved = svc["storage"].load_generated(pid, category_key)
            if saved and isinstance(saved.get("content"), dict):
                content = saved["content"]
                st.session_state[category_key] = content.get("items", {})
                st.session_state[f"{category_key}_checks"] = content.get("checks", {})
                return
        except Exception:
            pass
    st.session_state[category_key] = {}
    st.session_state[f"{category_key}_checks"] = {}


def _save_category_state(svc: dict, ensure_product_id, category_key: str,
                         compat_key: str):
    """Persist items to storage and update backward-compat combined text for dashboard."""
    items = st.session_state.get(category_key, {})
    checks = st.session_state.get(f"{category_key}_checks", {})
    pid = ensure_product_id()
    svc["storage"].save_generated(pid, category_key, {"items": items, "checks": checks})
    combined = combine_generated_items(items)
    if combined:
        st.session_state["generated"][compat_key] = combined


def _content_type_label(compat_key: str, is_ja: bool) -> str:
    if is_ja:
        return {
            "image_prompt": "画像プロンプト",
            "video_script": "動画台本",
            "ads_sns": "広告・SNS",
        }.get(compat_key, compat_key)
    return {
        "image_prompt": "prompt de imagem",
        "video_script": "roteiro de vídeo",
        "ads_sns": "anúncio/SNS",
    }.get(compat_key, compat_key)


def _render_inline_checks(svc: dict, ensure_product_id, category_key: str,
                          item_key: str, content: str, is_ja: bool, compat_key: str):
    checks_key = f"{category_key}_checks"
    st.session_state.setdefault(checks_key, {})
    item_checks = st.session_state[checks_key].get(item_key, {})
    current_content = st.session_state.get(f"ta_{category_key}_{item_key}", content)
    core = st.session_state.get("core_text", "")

    st.markdown('<div class="cs-info">💡 ' + (
        "生成結果がCoreと合っているか、誇大表現がないかを確認します。"
        if is_ja else
        "Verifica se o conteúdo está alinhado ao Core e se há expressões de risco."
    ) + '</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 " + ("品質チェック" if is_ja else "Verificar qualidade"),
                     key=f"quality_{category_key}_{item_key}", use_container_width=True):
            with st.spinner("チェック中..." if is_ja else "Verificando..."):
                result = svc["checker"].check_consistency(
                    core, current_content, _content_type_label(compat_key, is_ja)
                )
                item_checks["quality"] = result
                st.session_state[checks_key][item_key] = item_checks
                _save_category_state(svc, ensure_product_id, category_key, compat_key)
            st.rerun()
    with col2:
        if st.button("⚠️ " + ("リスク表現チェック" if is_ja else "Verificar riscos"),
                     key=f"risk_{category_key}_{item_key}", use_container_width=True):
            with st.spinner("チェック中..." if is_ja else "Verificando..."):
                result = svc["checker"].check_risk_expressions(current_content)
                item_checks["risk"] = result
                st.session_state[checks_key][item_key] = item_checks
                _save_category_state(svc, ensure_product_id, category_key, compat_key)
            st.rerun()

    if item_checks.get("quality"):
        st.markdown("**" + ("品質チェック結果" if is_ja else "Resultado de qualidade") + "**")
        st.markdown(
            f'<div class="gen-check-box">{_esc(item_checks["quality"])}</div>',
            unsafe_allow_html=True,
        )
    if item_checks.get("risk"):
        st.markdown("**" + ("リスク表現チェック結果" if is_ja else "Resultado de riscos") + "**")
        st.markdown(
            f'<div class="gen-check-box">{_esc(item_checks["risk"])}</div>',
            unsafe_allow_html=True,
        )


def _render_improve_tools(svc: dict, ensure_product_id, category_key: str,
                          item_key: str, content: str, is_ja: bool, compat_key: str):
    checks = st.session_state.get(f"{category_key}_checks", {}).get(item_key, {})
    current_content = st.session_state.get(f"ta_{category_key}_{item_key}", content)
    core = st.session_state.get("core_text", "")
    content_type = _content_type_label(compat_key, is_ja)

    st.markdown('<div class="cs-info">💡 ' + (
        "目的に合わせて生成結果をワンクリックで改善します。改善後はこの結果に置き換わります。"
        if is_ja else
        _ui("", "Melhore o resultado com um clique. O conteúdo será substituído pela versão melhorada.", "Improve the result with one click. The improved version will replace this result.")
    ) + '</div>', unsafe_allow_html=True)

    improve_options = [
        ("shorten", _ui("短くする", "Encurtar", "Shorten")),
        ("natural", _ui("自然な日本語", "Mais natural", "Make natural")),
        ("premium", _ui("高級感を出す", "Mais premium", "Make premium")),
        ("ad_strong", _ui("広告向けに強く", "Mais forte para anúncio", "Strengthen for ads")),
        ("higgs", _ui("Higgs/生成AI向け", "Para Higgs/IA", "For Higgs / AI")),
    ]
    cols = st.columns(2)
    for i, (mode, label) in enumerate(improve_options):
        with cols[i % 2]:
            if st.button("✨ " + label, key=f"improve_{category_key}_{item_key}_{mode}",
                         use_container_width=True):
                notes = ""
                with st.spinner("改善中..." if is_ja else "Melhorando..."):
                    improved = svc["generator"].improve_generated_content(
                        current_content, core, content_type, mode, notes, _generation_market_options()
                    )
                    st.session_state[category_key][item_key] = improved
                    st.session_state[f"ta_{category_key}_{item_key}"] = improved
                    _save_category_state(svc, ensure_product_id, category_key, compat_key)
                st.rerun()


def _render_item_card(svc: dict, ensure_product_id, status_badge,
                      category_key: str, item_key: str, label: str, content: str,
                      regen_fn, is_ja: bool, compat_key: str):
    """Render an editable result card for one generated item."""
    pid = ensure_product_id()

    with st.expander(f"✅ {label}", expanded=True):
        st.markdown(
            '<div class="gen-result-head">'
            f'<div><div class="gen-result-title">{_esc(label)}</div>'
            f'<div class="gen-result-meta">{_esc("内容を確認して、必要なら編集してから保存してください。" if is_ja else "Revise, edite se necessário e salve.")}</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        tab_copy, tab_full, tab_improve = st.tabs([
            "コピー用に分ける" if is_ja else "Partes para copiar",
            "全文編集" if is_ja else "Editar texto completo",
            "改善" if is_ja else "Melhorar",
        ])
        with tab_copy:
            _render_copy_parts(category_key, item_key, content, is_ja)
        with tab_full:
            new_content = st.text_area(
                "全文" if is_ja else "Texto completo",
                value=content,
                height=300,
                key=f"ta_{category_key}_{item_key}",
                label_visibility="collapsed",
            )
        with tab_improve:
            _render_improve_tools(
                svc, ensure_product_id, category_key, item_key, content, is_ja, compat_key
            )
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 " + _ui("保存", "Salvar", "Save"),
                         key=f"save_{category_key}_{item_key}",
                         use_container_width=True, type="primary"):
                st.session_state[category_key][item_key] = st.session_state.get(
                    f"ta_{category_key}_{item_key}", content
                )
                _save_category_state(svc, ensure_product_id, category_key, compat_key)
                st.success("✅ " + _ui("保存しました", "Salvo!", "Saved!"))
        with col2:
            if st.button("🔄 " + _ui("再生成", "Regenerar", "Regenerate"),
                         key=f"regen_{category_key}_{item_key}",
                         use_container_width=True):
                with st.spinner("⏳ " + _ui("生成中...", "Gerando...", "Generating...")):
                    result = regen_fn(item_key)
                    st.session_state[category_key][item_key] = result
                    _save_category_state(svc, ensure_product_id, category_key, compat_key)
                st.rerun()
        with col3:
            safe_fname = item_key.replace("::", "_").replace("/", "_")
            st.download_button(
                "⬇️ " + _ui("ダウンロード", "Baixar", "Download"),
                data=content.encode("utf-8"),
                file_name=f"{safe_fname}.md",
                mime="text/markdown",
                key=f"dl_{category_key}_{item_key}",
                use_container_width=True,
            )


def page_image_prompt(svc: dict, t, ensure_product_id, status_badge):
    is_ja = st.session_state.get("lang", "ja") == "ja"
    lang = st.session_state.get("lang", "ja")
    st.markdown(_GEN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="section-header">🖼️ ' + t("image_prompt.title") + '</div>',
                unsafe_allow_html=True)

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + _ui("Core生成画面へ", "Ir para Gerar Core", "Go to Build Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    _load_category_state(svc, "image_prompts")
    core = st.session_state["core_text"]
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "")
    category = product_info.get("category", "")

    st.markdown(
        _hero(
            _ui("画像生成AIに貼るプロンプトを作る", "Criar prompts para IA de imagem", "Create prompts for image AI"),
            "ここでは画像そのものではなく、Higgsfield・Midjourney・画像生成AIに貼れる完成プロンプトを作ります。用途と雰囲気を先に決めると品質が安定します。"
            if is_ja else (
                "Here you create ready-to-paste prompts for Higgsfield, Midjourney, or other image AI tools. Setting use case and tone first improves quality."
                if lang == "en" else
                "Aqui você cria prompts prontos para Higgsfield, Midjourney ou outra IA de imagem. Definir uso e tom melhora a qualidade."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_info_grid([
        (_ui("Shopify用", "Para Shopify", "For Shopify"), "商品ページのFV・説明・使用シーンに使う画像案。" if is_ja else ("Image ideas for hero, explanation, and usage scenes." if lang == "en" else "Imagens para hero, explicação e uso.")),
        (_ui("SNS用", "Para SNS", "For social"), "Instagram投稿やストーリー向けの縦・正方形画像案。" if is_ja else ("Square and vertical image ideas for Instagram posts and stories." if lang == "en" else "Quadrado/vertical para Instagram e stories.")),
        (_ui("広告用", "Para anúncios", "For ads"), "視線を止める構図、悩み訴求、CTA前提の画像案。" if is_ja else ("Scroll-stopping composition, pain appeal, and CTA-aware image ideas." if lang == "en" else "Composição para parar o scroll e vender.")),
    ]), unsafe_allow_html=True)

    quality = _render_quality_controls("ip_quality", is_ja, "image")

    st.markdown("### " + _ui("プリセットを選ぶ", "Escolher preset", "Choose a preset"))
    preset_cols = st.columns(len(IP_PRESETS))
    for i, (pk, pja, ppt, pitems) in enumerate(IP_PRESETS):
        with preset_cols[i]:
            if st.button(_label_by_lang(pk, pja, ppt, IP_PRESET_EN), key=f"ip_preset_{pk}", use_container_width=True):
                for k, _, _ in IP_ITEMS:
                    st.session_state[f"chk_ip_{k}"] = (k in pitems)
                st.rerun()

    st.markdown("### " + _ui("生成する画像プロンプト", "Prompts de imagem", "Image prompts to generate"))
    selected = []
    selected_labels = []
    cols = st.columns(2)
    for i, (k, ja_lbl, pt_lbl) in enumerate(IP_ITEMS):
        with cols[i % 2]:
            default = st.session_state.get(f"chk_ip_{k}", False)
            label = _label_by_lang(k, ja_lbl, pt_lbl, IP_LABEL_EN)
            if st.checkbox(label, value=default, key=f"chk_ip_{k}"):
                selected.append(k)
                selected_labels.append(label)
            meta = _item_meta("ip", k, is_ja)
            if meta:
                st.caption(meta)

    _render_plan(selected_labels, quality, is_ja)
    n = len(selected)
    btn_label = _ui(f"⚡ 選択した {n} 項目を生成", f"⚡ Gerar {n} item(s) selecionado(s)", f"⚡ Generate {n} selected item(s)")
    if st.button(btn_label, type="primary", disabled=(n == 0)):
        prog = st.progress(0)
        status = st.empty()
        for i, k in enumerate(selected):
            lbl = next((_label_by_lang(kk, ja, pt, IP_LABEL_EN) for kk, ja, pt in IP_ITEMS if kk == k), k)
            status.text(f"⏳ {lbl} ({i+1}/{n})")
            result = svc["generator"].generate_image_prompt_item(k, core, product_name, category, quality)
            st.session_state["image_prompts"][k] = result
            prog.progress((i + 1) / n)
        status.empty()
        prog.empty()
        _save_category_state(svc, ensure_product_id, "image_prompts", "image_prompt")
        pid = ensure_product_id()
        svc["storage"].log_activity(pid, "画像プロンプト生成", f"{n}項目", "")
        st.rerun()

    items_data = st.session_state.get("image_prompts", {})
    has_results = any(items_data.get(k) for k, _, _ in IP_ITEMS)
    if has_results:
        st.markdown("### " + _ui("生成結果", "Resultados", "Results"))
        for k, ja_lbl, pt_lbl in IP_ITEMS:
            content = items_data.get(k)
            if not content:
                continue
            label = _label_by_lang(k, ja_lbl, pt_lbl, IP_LABEL_EN)

            def _make_regen_fn_ip(item_key):
                def _regen(_):
                    return svc["generator"].generate_image_prompt_item(
                        item_key, core, product_name, category, quality)
                return _regen

            _render_item_card(svc, ensure_product_id, status_badge,
                              "image_prompts", k, label, content,
                              _make_regen_fn_ip(k), is_ja, "image_prompt")
    else:
        st.markdown('<div class="cs-info">💡 ' + (
            "上の項目を選択して生成ボタンを押してください。" if is_ja
            else ("Select items above and click Generate." if lang == "en" else "Selecione os itens acima e clique em Gerar.")
        ) + '</div>', unsafe_allow_html=True)


def page_video_script(svc: dict, t, ensure_product_id, status_badge):
    is_ja = st.session_state.get("lang", "ja") == "ja"
    lang = st.session_state.get("lang", "ja")
    st.markdown(_GEN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎬 ' + t("video_script.title") + '</div>',
                unsafe_allow_html=True)

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + _ui("Core生成画面へ", "Ir para Gerar Core", "Go to Build Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    _load_category_state(svc, "video_scripts")
    core = st.session_state["core_text"]
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "")

    st.markdown(
        _hero(
            _ui("動画の台本・撮影指示・Higgs用プロンプトを作る", "Criar roteiro, direção e prompt Higgs", "Create video scripts, shooting direction, and Higgs prompts"),
            "秒数と用途を組み合わせて、ショート動画の設計図を作ります。広告用・SNS用・Higgs用で出力内容を変えます。"
            if is_ja else (
                "Combine duration and purpose to create a short-video blueprint. Output changes for ads, social posts, or Higgs."
                if lang == "en" else
                "Combine duração e uso para criar a estrutura do vídeo curto. A saída muda para anúncio, SNS ou Higgs."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_info_grid([
        (_ui("秒数", "Duração", "Duration"), "15秒はフック重視、30秒以上は理解と安心材料まで入れます。" if is_ja else ("15s focuses on the hook; 30s+ adds context and trust." if lang == "en" else "15s foca no gancho; 30s+ inclui contexto e confiança.")),
        (_ui("生成タイプ", "Tipo", "Type"), "TikTok、Reels、広告、撮影指示、Higgs用を選べます。" if is_ja else ("Choose TikTok, Reels, ads, shooting direction, or Higgs." if lang == "en" else "TikTok, Reels, anúncio, direção ou Higgs.")),
        (_ui("完成形", "Resultado", "Output"), "ナレーション・テロップ・映像指示まで分けて出します。" if is_ja else ("Outputs narration, on-screen captions, and visual direction separately." if lang == "en" else "Narração, legendas e direção visual separados.")),
    ]), unsafe_allow_html=True)

    quality = _render_quality_controls("vs_quality", is_ja, "video")

    _render_video_goal_cards(is_ja)

    with st.expander(_ui("細かいセットを選ぶ", "Escolher outros presets", "Choose detailed presets"), expanded=False):
        preset_cols = st.columns(len(VS_COMBO_PRESETS))
        for i, (pk, pja, ppt, durations, types) in enumerate(VS_COMBO_PRESETS):
            with preset_cols[i]:
                if st.button(_label_by_lang(pk, pja, ppt, VS_PRESET_EN), key=f"vs_preset_{pk}", use_container_width=True):
                    _set_video_selection(durations, types)
                    st.rerun()

    st.markdown("### " + _ui("2. 秒数を確認する", "2. Conferir duração", "2. Confirm duration"))
    selected_durations = []
    duration_cols = st.columns(len(VS_DURATIONS))
    for i, (k, ja_lbl, pt_lbl) in enumerate(VS_DURATIONS):
        with duration_cols[i]:
            default = st.session_state.get(f"chk_vs_duration_{k}", k in ("15s", "30s"))
            duration_label = ja_lbl if is_ja else pt_lbl
            if st.checkbox(duration_label, value=default, key=f"chk_vs_duration_{k}"):
                selected_durations.append(k)

    st.markdown("### " + _ui("3. 作る内容を確認する", "3. Conferir conteúdo", "3. Confirm output types"))
    selected_types = []
    type_groups = [
        (_ui("台本", "Roteiros", "Scripts"), {"tiktok", "reels", "yt_shorts", "ad_script"}),
        (_ui("制作素材", "Materiais", "Production assets"), {"narration", "timeline", "shooting"}),
        (_ui("AI用", "Para IA", "For AI"), {"higgs_marketing_studio"}),
    ]
    type_cols = st.columns(3)
    for col, (group_label, keys) in zip(type_cols, type_groups):
        with col:
            st.markdown("**" + group_label + "**")
            for k, ja_lbl, pt_lbl in VS_TYPES:
                if k not in keys:
                    continue
                default = st.session_state.get(f"chk_vs_type_{k}", False)
                label = _label_by_lang(k, ja_lbl, pt_lbl, VS_TYPE_EN)
                if st.checkbox(label, value=default, key=f"chk_vs_type_{k}"):
                    selected_types.append(k)
                meta = _item_meta("vs", k, is_ja)
                if meta:
                    st.caption(meta)

    selected = [(d, tp) for d in selected_durations for tp in selected_types]
    selected_labels = [_video_combo_label(d, tp, is_ja) for d, tp in selected]

    _render_plan(selected_labels, quality, is_ja)
    n = len(selected)
    btn_label = _ui(f"⚡ 選択した {n} 組み合わせを生成", f"⚡ Gerar {n} combinação(ões)", f"⚡ Generate {n} combination(s)")
    if st.button(btn_label, type="primary", disabled=(n == 0), key="vs_gen_btn"):
        prog = st.progress(0)
        status = st.empty()
        for i, (duration_key, type_key) in enumerate(selected):
            k = f"{duration_key}__{type_key}"
            lbl = _video_combo_label(duration_key, type_key, is_ja)
            status.text(f"⏳ {lbl} ({i+1}/{n})")
            result = svc["generator"].generate_video_script_combo(
                duration_key, type_key, core, product_name, quality)
            st.session_state["video_scripts"][k] = result
            prog.progress((i + 1) / n)
        status.empty()
        prog.empty()
        _save_category_state(svc, ensure_product_id, "video_scripts", "video_script")
        pid = ensure_product_id()
        svc["storage"].log_activity(pid, "動画台本生成", f"{n}項目", "")
        st.rerun()

    items_data = st.session_state.get("video_scripts", {})
    has_results = bool(items_data)
    if has_results:
        st.markdown("### " + _ui("生成結果", "Resultados", "Results"))
        for k, content in items_data.items():
            content = items_data.get(k)
            if not content:
                continue
            label = _video_item_label(k, is_ja)

            def _make_regen_fn_vs(item_key):
                def _regen(_):
                    if "__" in item_key:
                        duration_key, type_key = item_key.split("__", 1)
                        return svc["generator"].generate_video_script_combo(
                            duration_key, type_key, core, product_name, quality)
                    return svc["generator"].generate_video_script_item(item_key, core, product_name, quality)
                return _regen

            _render_item_card(svc, ensure_product_id, status_badge,
                              "video_scripts", k, label, content,
                              _make_regen_fn_vs(k), is_ja, "video_script")
    else:
        st.markdown('<div class="cs-info">💡 ' + (
            "秒数と生成タイプを選択して生成ボタンを押してください。" if is_ja
            else ("Select duration and type, then click Generate." if lang == "en" else "Selecione duração e tipo, depois clique em Gerar.")
        ) + '</div>', unsafe_allow_html=True)


def _video_combo_label(duration_key: str, type_key: str, is_ja: bool) -> str:
    duration = next((ja if is_ja else pt for k, ja, pt in VS_DURATIONS if k == duration_key), duration_key)
    type_label = next((_label_by_lang(k, ja, pt, VS_TYPE_EN) for k, ja, pt in VS_TYPES if k == type_key), type_key)
    return f"{duration} × {type_label}"


def _video_item_label(item_key: str, is_ja: bool) -> str:
    if "__" in item_key:
        duration_key, type_key = item_key.split("__", 1)
        return _video_combo_label(duration_key, type_key, is_ja)
    return next((_label_by_lang(k, ja, pt, VS_TYPE_EN) for k, ja, pt in VS_ITEMS if k == item_key), item_key)


def page_ads_sns(svc: dict, t, ensure_product_id, status_badge):
    is_ja = st.session_state.get("lang", "ja") == "ja"
    lang = st.session_state.get("lang", "ja")
    st.markdown(_GEN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="section-header">📣 ' + t("ads_sns.title") + '</div>',
                unsafe_allow_html=True)

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + _ui("Core生成画面へ", "Ir para Gerar Core", "Go to Build Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    _load_category_state(svc, "ads_sns_items")
    core = st.session_state["core_text"]
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "")

    st.markdown(
        _hero(
            _ui("広告・SNSの投稿文を媒体別に作る", "Criar textos de anúncio e SNS por canal", "Create ad and social copy by channel"),
            "媒体と目的を決めて、投稿文・広告コピー・CTA・ハッシュタグを作ります。生成予定の組み合わせを確認してから実行します。"
            if is_ja else (
                "Choose the channel and goal, then generate post copy, ad copy, CTAs, and hashtags. Review combinations before generating."
                if lang == "en" else
                "Escolha canal e objetivo para gerar posts, copies, CTAs e hashtags. Confira as combinações antes de gerar."
            ),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_info_grid([
        (_ui("媒体別", "Por canal", "By channel"), "Instagram、TikTok、Google広告など媒体の文脈に合わせます。" if is_ja else ("Adapts to Instagram, TikTok, Google Ads, and each channel context." if lang == "en" else "Adapta ao contexto de Instagram, TikTok, Google etc.")),
        (_ui("目的別", "Por objetivo", "By goal"), "投稿、広告コピー、CTA、ハッシュタグを分けて生成します。" if is_ja else ("Generates posts, ad copy, CTAs, and hashtags separately." if lang == "en" else "Separa post, copy, CTA e hashtags.")),
        (_ui("使いやすさ", "Pronto para uso", "Ready to use"), "複数案を出し、編集・保存・ダウンロードできます。" if is_ja else ("Creates editable and downloadable variations." if lang == "en" else "Gera variações editáveis e baixáveis.")),
    ]), unsafe_allow_html=True)

    quality = _render_quality_controls("as_quality", is_ja, "ads")

    st.markdown("### " + _ui("プリセットを選ぶ", "Escolher preset", "Choose a preset"))
    preset_cols = st.columns(len(AS_PRESETS))
    for i, (pk, pja, ppt, pcombos) in enumerate(AS_PRESETS):
        with preset_cols[i]:
            if st.button(_label_by_lang(pk, pja, ppt, AS_PRESET_EN), key=f"as_preset_{pk}", use_container_width=True):
                if pcombos:
                    preset_media = list({m for m, _ in pcombos})
                    preset_types = list({ct for _, ct in pcombos})
                    st.session_state["as_sel_media"] = preset_media
                    st.session_state["as_sel_types"] = preset_types
                    st.session_state["as_preset_combos"] = {f"{m}::{ct}" for m, ct in pcombos}
                else:
                    st.session_state["as_sel_media"] = []
                    st.session_state["as_sel_types"] = []
                    st.session_state["as_preset_combos"] = set()
                st.rerun()

    st.markdown("### " + _ui("媒体と生成タイプを選ぶ", "Escolher mídia e tipo", "Choose channel and output type"))
    col_media, col_type = st.columns(2)

    media_options = [m for m, _ in AS_MEDIA]
    media_labels = [lbl for _, lbl in AS_MEDIA]

    with col_media:
        st.markdown("**" + _ui("媒体", "Mídia", "Channel") + "**")
        sel_media_keys = st.session_state.get("as_sel_media", [])
        selected_media = []
        for mk, ml in zip(media_options, media_labels):
            default = mk in sel_media_keys
            if st.checkbox(ml, value=default, key=f"chk_as_m_{mk}"):
                selected_media.append(mk)
        st.session_state["as_sel_media"] = selected_media

    with col_type:
        st.markdown("**" + _ui("生成タイプ", "Tipo de Conteúdo", "Output type") + "**")
        sel_type_keys = st.session_state.get("as_sel_types", [])
        selected_types = []
        for tk, tja, tpt in AS_TYPES:
            default = tk in sel_type_keys
            label = _label_by_lang(tk, tja, tpt, AS_TYPE_EN)
            if st.checkbox(label, value=default, key=f"chk_as_t_{tk}"):
                selected_types.append(tk)
            meta = _item_meta("ads", tk, is_ja)
            if meta:
                st.caption(meta)
        st.session_state["as_sel_types"] = selected_types

    combos = [(m, ct) for m in selected_media for ct in selected_types]
    n = len(combos)
    selected_labels = []
    if n > 0:
        media_labels_map = {mk: ml for mk, ml in AS_MEDIA}
        type_labels_map = {k: _label_by_lang(k, ja, pt, AS_TYPE_EN) for k, ja, pt in AS_TYPES}
        selected_labels = [f"{media_labels_map[m]} / {type_labels_map[ct]}" for m, ct in combos]
    _render_plan(selected_labels, quality, is_ja)
    btn_label = _ui(f"⚡ {n} 組み合わせを生成", f"⚡ Gerar {n} combinação(ões)", f"⚡ Generate {n} combination(s)")
    if st.button(btn_label, type="primary", disabled=(n == 0), key="as_gen_btn"):
        prog = st.progress(0)
        status = st.empty()
        media_labels_map2 = {mk: ml for mk, ml in AS_MEDIA}
        type_labels_map2 = {k: _label_by_lang(k, ja, pt, AS_TYPE_EN) for k, ja, pt in AS_TYPES}
        for i, (m, ct) in enumerate(combos):
            combo_label = f"{media_labels_map2[m]} / {type_labels_map2[ct]}"
            status.text(f"⏳ {combo_label} ({i+1}/{n})")
            result = svc["generator"].generate_ads_sns_item(m, ct, core, product_name, quality)
            st.session_state["ads_sns_items"][f"{m}::{ct}"] = result
            prog.progress((i + 1) / n)
        status.empty()
        prog.empty()
        _save_category_state(svc, ensure_product_id, "ads_sns_items", "ads_sns")
        pid = ensure_product_id()
        svc["storage"].log_activity(pid, "広告・SNS生成", f"{n}組み合わせ", "")
        st.rerun()

    items_data = st.session_state.get("ads_sns_items", {})
    if items_data:
        st.markdown("### " + _ui("生成結果", "Resultados", "Results"))
        media_labels_map3 = {mk: ml for mk, ml in AS_MEDIA}
        type_labels_map3 = {k: _label_by_lang(k, ja, pt, AS_TYPE_EN) for k, ja, pt in AS_TYPES}

        for mk, ml in AS_MEDIA:
            media_items = {k: v for k, v in items_data.items()
                           if k.startswith(f"{mk}::") and v}
            if not media_items:
                continue
            st.markdown(f"#### {ml}")
            for item_key, content in media_items.items():
                parts = item_key.split("::", 1)
                ct = parts[1] if len(parts) == 2 else item_key
                label = f"{ml} - {type_labels_map3.get(ct, ct)}"

                def _make_regen_fn_as(media_key, content_type_key):
                    def _regen(_):
                        return svc["generator"].generate_ads_sns_item(
                            media_key, content_type_key, core, product_name, quality)
                    return _regen

                _render_item_card(svc, ensure_product_id, status_badge,
                                  "ads_sns_items", item_key, label, content,
                                  _make_regen_fn_as(mk, ct), is_ja, "ads_sns")
    else:
        st.markdown('<div class="cs-info">💡 ' + (
            "上の媒体と生成タイプを選択して生成ボタンを押してください。" if is_ja
            else ("Select channel and output type above, then click Generate." if lang == "en" else "Selecione mídia e tipo acima e clique em Gerar.")
        ) + '</div>', unsafe_allow_html=True)
