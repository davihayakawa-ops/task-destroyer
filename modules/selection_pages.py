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


def _load_category_state(svc: dict, category_key: str):
    """Load per-item results from storage if not already in session_state."""
    if category_key in st.session_state:
        return
    pid = st.session_state.get("product_id", "")
    if pid:
        try:
            saved = svc["storage"].load_generated(pid, category_key)
            if saved and isinstance(saved.get("content"), dict):
                st.session_state[category_key] = saved["content"].get("items", {})
                return
        except Exception:
            pass
    st.session_state[category_key] = {}


def _save_category_state(svc: dict, ensure_product_id, category_key: str,
                         compat_key: str):
    """Persist items to storage and update backward-compat combined text for dashboard."""
    items = st.session_state.get(category_key, {})
    pid = ensure_product_id()
    svc["storage"].save_generated(pid, category_key, {"items": items})
    combined = combine_generated_items(items)
    if combined:
        st.session_state["generated"][compat_key] = combined


def _render_item_card(svc: dict, ensure_product_id, status_badge,
                      category_key: str, item_key: str, label: str, content: str,
                      regen_fn, is_ja: bool, compat_key: str):
    """Render an editable result card for one generated item."""
    pid = ensure_product_id()

    with st.expander(f"✅ {label}", expanded=True):
        new_content = st.text_area(
            "",
            value=content,
            height=300,
            key=f"ta_{category_key}_{item_key}",
            label_visibility="collapsed",
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 " + ("保存" if is_ja else "Salvar"),
                         key=f"save_{category_key}_{item_key}",
                         use_container_width=True, type="primary"):
                st.session_state[category_key][item_key] = new_content
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

    st.markdown("### " + ("STEP 1: プリセット選択" if is_ja else "STEP 1: Selecionar Preset"))
    preset_cols = st.columns(len(IP_PRESETS))
    for i, (pk, pja, ppt, pitems) in enumerate(IP_PRESETS):
        with preset_cols[i]:
            if st.button(pja if is_ja else ppt, key=f"ip_preset_{pk}", use_container_width=True):
                for k, _, _ in IP_ITEMS:
                    st.session_state[f"chk_ip_{k}"] = (k in pitems)
                st.rerun()

    st.markdown("### " + ("STEP 2: 生成項目を選択" if is_ja else "STEP 2: Selecionar Itens"))
    selected = []
    cols = st.columns(2)
    for i, (k, ja_lbl, pt_lbl) in enumerate(IP_ITEMS):
        with cols[i % 2]:
            default = st.session_state.get(f"chk_ip_{k}", False)
            if st.checkbox(ja_lbl if is_ja else pt_lbl, value=default, key=f"chk_ip_{k}"):
                selected.append(k)

    st.markdown("---")
    n = len(selected)
    btn_label = (f"⚡ 選択した {n} 項目を生成" if is_ja else f"⚡ Gerar {n} item(s) selecionado(s)")
    if st.button(btn_label, type="primary", disabled=(n == 0)):
        prog = st.progress(0)
        status = st.empty()
        for i, k in enumerate(selected):
            lbl = next((ja if is_ja else pt for kk, ja, pt in IP_ITEMS if kk == k), k)
            status.text(f"⏳ {lbl} ({i+1}/{n})")
            result = svc["generator"].generate_image_prompt_item(k, core, product_name, category)
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
                        item_key, core, product_name, category)
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

    st.markdown("### " + ("STEP 1: プリセット選択" if is_ja else "STEP 1: Selecionar Preset"))
    preset_cols = st.columns(len(VS_COMBO_PRESETS))
    for i, (pk, pja, ppt, durations, types) in enumerate(VS_COMBO_PRESETS):
        with preset_cols[i]:
            if st.button(pja if is_ja else ppt, key=f"vs_preset_{pk}", use_container_width=True):
                for k, _, _ in VS_DURATIONS:
                    st.session_state[f"chk_vs_duration_{k}"] = (k in durations)
                for k, _, _ in VS_TYPES:
                    st.session_state[f"chk_vs_type_{k}"] = (k in types)
                st.rerun()

    st.markdown("### " + ("STEP 2: 秒数を選択" if is_ja else "STEP 2: Selecionar Duração"))
    selected_durations = []
    duration_cols = st.columns(len(VS_DURATIONS))
    for i, (k, ja_lbl, pt_lbl) in enumerate(VS_DURATIONS):
        with duration_cols[i]:
            default = st.session_state.get(f"chk_vs_duration_{k}", k in ("15s", "30s"))
            if st.checkbox(ja_lbl if is_ja else pt_lbl, value=default, key=f"chk_vs_duration_{k}"):
                selected_durations.append(k)

    st.markdown("### " + ("STEP 3: 生成タイプを選択" if is_ja else "STEP 3: Selecionar Tipo"))
    selected_types = []
    type_cols = st.columns(2)
    for i, (k, ja_lbl, pt_lbl) in enumerate(VS_TYPES):
        with type_cols[i % 2]:
            default = st.session_state.get(f"chk_vs_type_{k}", k in ("tiktok", "reels"))
            if st.checkbox(ja_lbl if is_ja else pt_lbl, value=default, key=f"chk_vs_type_{k}"):
                selected_types.append(k)

    selected = [(d, tp) for d in selected_durations for tp in selected_types]

    st.markdown("---")
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
                duration_key, type_key, core, product_name)
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
                            duration_key, type_key, core, product_name)
                    return svc["generator"].generate_video_script_item(item_key, core, product_name)
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

    st.markdown("### " + ("STEP 1: プリセット選択" if is_ja else "STEP 1: Selecionar Preset"))
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

    st.markdown("### " + ("STEP 2: 媒体と生成タイプを選択" if is_ja
                          else "STEP 2: Selecionar Mídia e Tipo"))
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
        st.session_state["as_sel_types"] = selected_types

    st.markdown("---")
    combos = [(m, ct) for m in selected_media for ct in selected_types]
    n = len(combos)
    if n > 0:
        media_labels_map = {mk: ml for mk, ml in AS_MEDIA}
        type_labels_map = {k: (ja if is_ja else pt) for k, ja, pt in AS_TYPES}
        st.info(("生成する組み合わせ: " if is_ja else "Combinações a gerar: ") +
                ", ".join(f"{media_labels_map[m]}/{type_labels_map[ct]}" for m, ct in combos))
    btn_label = (f"⚡ {n} 組み合わせを生成" if is_ja else f"⚡ Gerar {n} combinação(ões)")
    if st.button(btn_label, type="primary", disabled=(n == 0), key="as_gen_btn"):
        prog = st.progress(0)
        status = st.empty()
        media_labels_map2 = {mk: ml for mk, ml in AS_MEDIA}
        type_labels_map2 = {k: (ja if is_ja else pt) for k, ja, pt in AS_TYPES}
        for i, (m, ct) in enumerate(combos):
            combo_label = f"{media_labels_map2[m]} / {type_labels_map2[ct]}"
            status.text(f"⏳ {combo_label} ({i+1}/{n})")
            result = svc["generator"].generate_ads_sns_item(m, ct, core, product_name)
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
                            media_key, content_type_key, core, product_name)
                    return _regen

                _render_item_card(svc, ensure_product_id, status_badge,
                                  "ads_sns_items", item_key, label, content,
                                  _make_regen_fn_as(mk, ct), is_ja, "ads_sns")
    else:
        st.markdown('<div class="cs-info">💡 ' + (
            "上の媒体と生成タイプを選択して生成ボタンを押してください。" if is_ja
            else "Selecione mídia e tipo acima e clique em Gerar."
        ) + '</div>', unsafe_allow_html=True)
