"""i18n helpers for Task Destroyer / core_studio.

Extracted from app.py. Uses ROOT = project root (parent of modules/).
"""

import json
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_i18n(lang: str) -> dict:
    path = ROOT / "i18n" / f"{lang}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def t(key_path: str):
    """Get translation value (str or list) by dot-separated key path."""
    i18n = st.session_state.get("i18n", {})
    keys = key_path.split(".")
    val = i18n
    for k in keys:
        if not isinstance(val, dict):
            return key_path
        val = val.get(k)
        if val is None:
            return key_path
    if isinstance(val, (str, list)):
        return val
    return key_path


def tl(key_path: str) -> list:
    """Get a translation list. Returns [] if the key is missing or not a list."""
    val = t(key_path)
    return val if isinstance(val, list) else []


def resolve_option_index(saved: str, opts: list, opts_other: list) -> int:
    """Return the index of saved in opts, falling back to opts_other for cross-language mapping."""
    if not saved:
        return 0
    for i, o in enumerate(opts):
        if o == saved:
            return i
    for i, o in enumerate(opts_other):
        if o == saved:
            return min(i, len(opts) - 1)
    return len(opts) - 1  # default: last item (free input or last option)
