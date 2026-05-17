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


def _render_quality_controls(prefix: str, is_ja: bool, page_kind: str) -> dict:
    st.markdown("### " + ("生成の方向性" if is_ja else "Direção da geração"))
    if page_kind == "image":
        purpose_opts = ["Shopify商品ページ", "広告バナー", "SNS投稿", "Higgsfield/画像AI用", "高級ブランド風"]
        purpose_pt = ["Página Shopify", "Banner de anúncio", "Post SNS", "Para Higgsfield/IA de imagem", "Marca premium"]
    elif page_kind == "video":
        purpose_opts = ["TikTok/Reels", "YouTube Shorts", "広告動画", "Higgs Marketing Studio用", "撮影指示用"]
        purpose_pt = ["TikTok/Reels", "YouTube Shorts", "Vídeo de anúncio", "Para Higgs Marketing Studio", "Direção de filmagem"]
    else:
        purpose_opts = ["通常投稿", "広告運用", "商品ページ誘導", "キャンペーン", "コメント獲得"]
        purpose_pt = ["Post normal", "Anúncio pago", "Levar à página do produto", "Campanha", "Gerar comentários"]
    tone_opts = ["上品・信頼感", "ナチュラル", "高級感", "悩み共感", "SNS広告・強め", "ミニマル"]
    tone_pt = ["Elegante/confiável", "Natural", "Premium", "Empatia com dor", "Anúncio SNS forte", "Minimalista"]
    strength_opts = ["控えめ", "標準", "強め"]
    strength_pt = ["Suave", "Padrão", "Forte"]

    col1, col2, col3 = st.columns(3)
    with col1:
        purpose = st.selectbox(
            "用途" if is_ja else "Uso",
            purpose_opts if is_ja else purpose_pt,
            key=f"{prefix}_purpose",
        )
    with col2:
        tone = st.selectbox(
            "雰囲気" if is_ja else "Tom",
            tone_opts if is_ja else tone_pt,
            key=f"{prefix}_tone",
        )
    with col3:
        strength = st.selectbox(
            "訴求の強さ" if is_ja else "Força",
            strength_opts if is_ja else strength_pt,
            index=1,
            key=f"{prefix}_strength",
        )
    note = st.text_input(
        "追加指示（任意）" if is_ja else "Instrução extra (opcional)",
        placeholder=("例：黒背景、高級感、30代女性向け" if is_ja else "Ex.: fundo escuro, premium, mulheres 30+"),
        key=f"{prefix}_note",
    )
    return {
        "purpose": purpose,
        "tone": tone,
        "strength": strength,
        "note": note,
    }


def _render_plan(selected_labels, quality: dict, is_ja: bool):
    if not selected_labels:
        msg = "まだ生成対象が選ばれていません。" if is_ja else "Nenhum item selecionado ainda."
        st.markdown(f'<div class="gen-plan">{_esc(msg)}</div>', unsafe_allow_html=True)
        return
    title = "生成予定" if is_ja else "Será gerado"
    settings = (
        f"{'用途' if is_ja else 'Uso'}: {quality.get('purpose', '-')}"
        f" / {'雰囲気' if is_ja else 'Tom'}: {quality.get('tone', '-')}"
        f" / {'強さ' if is_ja else 'Força'}: {quality.get('strength', '-')}"
    )
    pills = "".join(f'<span class="gen-pill">{_esc(label)}</span>' for label in selected_labels)
    st.markdown(
        f'<div class="gen-plan"><strong>{_esc(title)}: {len(selected_labels)}</strong><br>'
        f'{_esc(settings)}<br>{pills}</div>',
        unsafe_allow_html=True,
    )


def _item_meta(category: str, key: str, is_ja: bool) -> str:
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
    ja, pt = data.get(key, ("", ""))
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
    if category_key == "image_prompts":
        return [
            ("生成AIプロンプト（英語）" if is_ja else "Prompt em inglês", _extract_markdown_section(content, "生成AIプロンプト（英語）")),
            ("日本語メモ" if is_ja else "Notas", _extract_markdown_section(content, "日本語メモ（制作担当者への補足）") or _extract_markdown_section(content, "日本語メモ")),
            ("NG要素" if is_ja else "Itens proibidos", _extract_markdown_section(content, "NG要素")),
            ("入れると良いテキスト" if is_ja else "Texto recomendado", _extract_markdown_section(content, "入れると良いテキスト")),
        ]
    if category_key == "video_scripts":
        if "higgs_marketing_studio" in item_key:
            return [
                ("Higgs用プロンプト" if is_ja else "Prompt Higgs", _extract_markdown_section(content, "Higgs Marketing Studio Prompt") or content),
                ("Scene direction" if is_ja else "Direção de cenas", _extract_markdown_section(content, "Scene-by-scene Direction")),
                ("Voiceover" if is_ja else "Voiceover", _extract_markdown_section(content, "Voiceover Script")),
                ("日本語メモ" if is_ja else "Notas", _extract_markdown_section(content, "日本語メモ")),
            ]
        return [
            ("冒頭3秒フック" if is_ja else "Gancho inicial", _extract_markdown_section(content, "冒頭3秒フック")),
            ("完成台本" if is_ja else "Roteiro completo", _extract_markdown_section(content, "完成台本")),
            ("ナレーション" if is_ja else "Narração", _extract_markdown_section(content, "ナレーション")),
            ("テロップ" if is_ja else "Legendas", _extract_markdown_section(content, "テロップ")),
            ("映像・撮影指示" if is_ja else "Direção visual", _extract_markdown_section(content, "映像・撮影指示")),
            ("CTA案" if is_ja else "CTAs", _extract_markdown_section(content, "CTA案 3つ") or _extract_markdown_section(content, "CTA案")),
        ]
    if category_key == "ads_sns_items":
        return [
            ("案1" if is_ja else "Opção 1", _extract_markdown_section(content, "案1")),
            ("案2" if is_ja else "Opção 2", _extract_markdown_section(content, "案2")),
            ("案3" if is_ja else "Opção 3", _extract_markdown_section(content, "案3")),
            ("短縮版" if is_ja else "Versão curta", _extract_markdown_section(content, "短縮版")),
            ("CTA" if is_ja else "CTA", _extract_markdown_section(content, "CTA")),
            ("注意点" if is_ja else "Cuidados", _extract_markdown_section(content, "注意点")),
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
        "⬇️ " + ("この部分をダウンロード" if is_ja else "Baixar esta parte"),
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
        tab_copy, tab_full, tab_check = st.tabs([
            "コピー用に分ける" if is_ja else "Partes para copiar",
            "全文編集" if is_ja else "Editar texto completo",
            "チェック" if is_ja else "Verificar",
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
        with tab_check:
            _render_inline_checks(
                svc, ensure_product_id, category_key, item_key, content, is_ja, compat_key
            )
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 " + ("保存" if is_ja else "Salvar"),
                         key=f"save_{category_key}_{item_key}",
                         use_container_width=True, type="primary"):
                st.session_state[category_key][item_key] = st.session_state.get(
                    f"ta_{category_key}_{item_key}", content
                )
                _save_category_state(svc, ensure_product_id, category_key, compat_key)
                st.success("✅ " + ("保存しました" if is_ja else "Salvo!"))
        with col2:
            if st.button("🔄 " + ("再生成" if is_ja else "Regenerar"),
                         key=f"regen_{category_key}_{item_key}",
                         use_container_width=True):
                with st.spinner("⏳ " + ("生成中..." if is_ja else "Gerando...")):
                    result = regen_fn(item_key)
                    st.session_state[category_key][item_key] = result
                    _save_category_state(svc, ensure_product_id, category_key, compat_key)
                st.rerun()
        with col3:
            safe_fname = item_key.replace("::", "_").replace("/", "_")
            st.download_button(
                "⬇️ " + ("ダウンロード" if is_ja else "Baixar"),
                data=content.encode("utf-8"),
                file_name=f"{safe_fname}.md",
                mime="text/markdown",
                key=f"dl_{category_key}_{item_key}",
                use_container_width=True,
            )


def page_image_prompt(svc: dict, t, ensure_product_id, status_badge):
    is_ja = st.session_state.get("lang", "ja") == "ja"
    st.markdown(_GEN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="section-header">🖼️ ' + t("image_prompt.title") + '</div>',
                unsafe_allow_html=True)

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + ("Core生成画面へ" if is_ja else "Ir para Gerar Core")):
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
            "画像生成AIに貼るプロンプトを作る" if is_ja else "Criar prompts para IA de imagem",
            "ここでは画像そのものではなく、Higgsfield・Midjourney・画像生成AIに貼れる完成プロンプトを作ります。用途と雰囲気を先に決めると品質が安定します。"
            if is_ja else
            "Aqui você cria prompts prontos para Higgsfield, Midjourney ou outra IA de imagem. Definir uso e tom melhora a qualidade.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_info_grid([
        ("Shopify用" if is_ja else "Para Shopify", "商品ページのFV・説明・使用シーンに使う画像案。" if is_ja else "Imagens para hero, explicação e uso."),
        ("SNS用" if is_ja else "Para SNS", "Instagram投稿やストーリー向けの縦・正方形画像案。" if is_ja else "Quadrado/vertical para Instagram e stories."),
        ("広告用" if is_ja else "Para anúncios", "視線を止める構図、悩み訴求、CTA前提の画像案。" if is_ja else "Composição para parar o scroll e vender."),
    ]), unsafe_allow_html=True)

    quality = _render_quality_controls("ip_quality", is_ja, "image")

    st.markdown("### " + ("プリセットを選ぶ" if is_ja else "Escolher preset"))
    preset_cols = st.columns(len(IP_PRESETS))
    for i, (pk, pja, ppt, pitems) in enumerate(IP_PRESETS):
        with preset_cols[i]:
            if st.button(pja if is_ja else ppt, key=f"ip_preset_{pk}", use_container_width=True):
                for k, _, _ in IP_ITEMS:
                    st.session_state[f"chk_ip_{k}"] = (k in pitems)
                st.rerun()

    st.markdown("### " + ("生成する画像プロンプト" if is_ja else "Prompts de imagem"))
    selected = []
    selected_labels = []
    cols = st.columns(2)
    for i, (k, ja_lbl, pt_lbl) in enumerate(IP_ITEMS):
        with cols[i % 2]:
            default = st.session_state.get(f"chk_ip_{k}", False)
            if st.checkbox(ja_lbl if is_ja else pt_lbl, value=default, key=f"chk_ip_{k}"):
                selected.append(k)
                selected_labels.append(ja_lbl if is_ja else pt_lbl)
            meta = _item_meta("ip", k, is_ja)
            if meta:
                st.caption(meta)

    _render_plan(selected_labels, quality, is_ja)
    n = len(selected)
    btn_label = (f"⚡ 選択した {n} 項目を生成" if is_ja else f"⚡ Gerar {n} item(s) selecionado(s)")
    if st.button(btn_label, type="primary", disabled=(n == 0)):
        prog = st.progress(0)
        status = st.empty()
        for i, k in enumerate(selected):
            lbl = next((ja if is_ja else pt for kk, ja, pt in IP_ITEMS if kk == k), k)
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
        st.markdown("### " + ("生成結果" if is_ja else "Resultados"))
        for k, ja_lbl, pt_lbl in IP_ITEMS:
            content = items_data.get(k)
            if not content:
                continue
            label = ja_lbl if is_ja else pt_lbl

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
            else "Selecione os itens acima e clique em Gerar."
        ) + '</div>', unsafe_allow_html=True)


def page_video_script(svc: dict, t, ensure_product_id, status_badge):
    is_ja = st.session_state.get("lang", "ja") == "ja"
    st.markdown(_GEN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎬 ' + t("video_script.title") + '</div>',
                unsafe_allow_html=True)

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + ("Core生成画面へ" if is_ja else "Ir para Gerar Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    _load_category_state(svc, "video_scripts")
    core = st.session_state["core_text"]
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "")

    st.markdown(
        _hero(
            "動画の台本・撮影指示・Higgs用プロンプトを作る" if is_ja else "Criar roteiro, direção e prompt Higgs",
            "秒数と用途を組み合わせて、ショート動画の設計図を作ります。広告用・SNS用・Higgs用で出力内容を変えます。"
            if is_ja else
            "Combine duração e uso para criar a estrutura do vídeo curto. A saída muda para anúncio, SNS ou Higgs.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_info_grid([
        ("秒数" if is_ja else "Duração", "15秒はフック重視、30秒以上は理解と安心材料まで入れます。" if is_ja else "15s foca no gancho; 30s+ inclui contexto e confiança."),
        ("生成タイプ" if is_ja else "Tipo", "TikTok、Reels、広告、撮影指示、Higgs用を選べます。" if is_ja else "TikTok, Reels, anúncio, direção ou Higgs."),
        ("完成形" if is_ja else "Resultado", "ナレーション・テロップ・映像指示まで分けて出します。" if is_ja else "Narração, legendas e direção visual separados."),
    ]), unsafe_allow_html=True)

    quality = _render_quality_controls("vs_quality", is_ja, "video")

    st.markdown("### " + ("プリセットを選ぶ" if is_ja else "Escolher preset"))
    preset_cols = st.columns(len(VS_COMBO_PRESETS))
    for i, (pk, pja, ppt, durations, types) in enumerate(VS_COMBO_PRESETS):
        with preset_cols[i]:
            if st.button(pja if is_ja else ppt, key=f"vs_preset_{pk}", use_container_width=True):
                for k, _, _ in VS_DURATIONS:
                    st.session_state[f"chk_vs_duration_{k}"] = (k in durations)
                for k, _, _ in VS_TYPES:
                    st.session_state[f"chk_vs_type_{k}"] = (k in types)
                st.rerun()

    st.markdown("### " + ("秒数を選ぶ" if is_ja else "Escolher duração"))
    selected_durations = []
    duration_cols = st.columns(len(VS_DURATIONS))
    for i, (k, ja_lbl, pt_lbl) in enumerate(VS_DURATIONS):
        with duration_cols[i]:
            default = st.session_state.get(f"chk_vs_duration_{k}", k in ("15s", "30s"))
            if st.checkbox(ja_lbl if is_ja else pt_lbl, value=default, key=f"chk_vs_duration_{k}"):
                selected_durations.append(k)

    st.markdown("### " + ("作る内容を選ぶ" if is_ja else "Escolher conteúdo"))
    selected_types = []
    type_cols = st.columns(2)
    for i, (k, ja_lbl, pt_lbl) in enumerate(VS_TYPES):
        with type_cols[i % 2]:
            default = st.session_state.get(f"chk_vs_type_{k}", k in ("tiktok", "reels"))
            if st.checkbox(ja_lbl if is_ja else pt_lbl, value=default, key=f"chk_vs_type_{k}"):
                selected_types.append(k)
            meta = _item_meta("vs", k, is_ja)
            if meta:
                st.caption(meta)

    selected = [(d, tp) for d in selected_durations for tp in selected_types]
    selected_labels = [_video_combo_label(d, tp, is_ja) for d, tp in selected]

    _render_plan(selected_labels, quality, is_ja)
    n = len(selected)
    btn_label = (f"⚡ 選択した {n} 組み合わせを生成" if is_ja else f"⚡ Gerar {n} combinação(ões)")
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
        st.markdown("### " + ("生成結果" if is_ja else "Resultados"))
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
            else "Selecione duração e tipo, depois clique em Gerar."
        ) + '</div>', unsafe_allow_html=True)


def _video_combo_label(duration_key: str, type_key: str, is_ja: bool) -> str:
    duration = next((ja if is_ja else pt for k, ja, pt in VS_DURATIONS if k == duration_key), duration_key)
    type_label = next((ja if is_ja else pt for k, ja, pt in VS_TYPES if k == type_key), type_key)
    return f"{duration} × {type_label}"


def _video_item_label(item_key: str, is_ja: bool) -> str:
    if "__" in item_key:
        duration_key, type_key = item_key.split("__", 1)
        return _video_combo_label(duration_key, type_key, is_ja)
    return next((ja if is_ja else pt for k, ja, pt in VS_ITEMS if k == item_key), item_key)


def page_ads_sns(svc: dict, t, ensure_product_id, status_badge):
    is_ja = st.session_state.get("lang", "ja") == "ja"
    st.markdown(_GEN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="section-header">📣 ' + t("ads_sns.title") + '</div>',
                unsafe_allow_html=True)

    if not st.session_state.get("core_text"):
        st.markdown('<div class="cs-warning">⚠️ ' + t("common.no_core_warning") + '</div>',
                    unsafe_allow_html=True)
        if st.button("✨ " + ("Core生成画面へ" if is_ja else "Ir para Gerar Core")):
            st.session_state["page"] = "core_generation"
            st.rerun()
        return

    _load_category_state(svc, "ads_sns_items")
    core = st.session_state["core_text"]
    product_info = st.session_state.get("product_info", {})
    product_name = product_info.get("name", "")

    st.markdown(
        _hero(
            "広告・SNSの投稿文を媒体別に作る" if is_ja else "Criar textos de anúncio e SNS por canal",
            "媒体と目的を決めて、投稿文・広告コピー・CTA・ハッシュタグを作ります。生成予定の組み合わせを確認してから実行します。"
            if is_ja else
            "Escolha canal e objetivo para gerar posts, copies, CTAs e hashtags. Confira as combinações antes de gerar.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_info_grid([
        ("媒体別" if is_ja else "Por canal", "Instagram、TikTok、Google広告など媒体の文脈に合わせます。" if is_ja else "Adapta ao contexto de Instagram, TikTok, Google etc."),
        ("目的別" if is_ja else "Por objetivo", "投稿、広告コピー、CTA、ハッシュタグを分けて生成します。" if is_ja else "Separa post, copy, CTA e hashtags."),
        ("使いやすさ" if is_ja else "Pronto para uso", "複数案を出し、編集・保存・ダウンロードできます。" if is_ja else "Gera variações editáveis e baixáveis."),
    ]), unsafe_allow_html=True)

    quality = _render_quality_controls("as_quality", is_ja, "ads")

    st.markdown("### " + ("プリセットを選ぶ" if is_ja else "Escolher preset"))
    preset_cols = st.columns(len(AS_PRESETS))
    for i, (pk, pja, ppt, pcombos) in enumerate(AS_PRESETS):
        with preset_cols[i]:
            if st.button(pja if is_ja else ppt, key=f"as_preset_{pk}", use_container_width=True):
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

    st.markdown("### " + ("媒体と生成タイプを選ぶ" if is_ja
                          else "Escolher mídia e tipo"))
    col_media, col_type = st.columns(2)

    media_options = [m for m, _ in AS_MEDIA]
    media_labels = [lbl for _, lbl in AS_MEDIA]

    with col_media:
        st.markdown("**" + ("媒体" if is_ja else "Mídia") + "**")
        sel_media_keys = st.session_state.get("as_sel_media", [])
        selected_media = []
        for mk, ml in zip(media_options, media_labels):
            default = mk in sel_media_keys
            if st.checkbox(ml, value=default, key=f"chk_as_m_{mk}"):
                selected_media.append(mk)
        st.session_state["as_sel_media"] = selected_media

    with col_type:
        st.markdown("**" + ("生成タイプ" if is_ja else "Tipo de Conteúdo") + "**")
        sel_type_keys = st.session_state.get("as_sel_types", [])
        selected_types = []
        for tk, tja, tpt in AS_TYPES:
            default = tk in sel_type_keys
            if st.checkbox(tja if is_ja else tpt, value=default, key=f"chk_as_t_{tk}"):
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
        type_labels_map = {k: (ja if is_ja else pt) for k, ja, pt in AS_TYPES}
        selected_labels = [f"{media_labels_map[m]} / {type_labels_map[ct]}" for m, ct in combos]
    _render_plan(selected_labels, quality, is_ja)
    btn_label = (f"⚡ {n} 組み合わせを生成" if is_ja else f"⚡ Gerar {n} combinação(ões)")
    if st.button(btn_label, type="primary", disabled=(n == 0), key="as_gen_btn"):
        prog = st.progress(0)
        status = st.empty()
        media_labels_map2 = {mk: ml for mk, ml in AS_MEDIA}
        type_labels_map2 = {k: (ja if is_ja else pt) for k, ja, pt in AS_TYPES}
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
        st.markdown("### " + ("生成結果" if is_ja else "Resultados"))
        media_labels_map3 = {mk: ml for mk, ml in AS_MEDIA}
        type_labels_map3 = {k: (ja if is_ja else pt) for k, ja, pt in AS_TYPES}

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
            else "Selecione mídia e tipo acima e clique em Gerar."
        ) + '</div>', unsafe_allow_html=True)
