"""Mode registry — add new modes here to make them available in the UI."""

MODES = {
    "commerce": {
        "id": "commerce",
        "name_ja": "Commerce Mode",
        "name_pt": "Modo Commerce",
        "name_en": "Commerce Mode",
        "desc_ja": "Shopify商品ページ、広告、画像・動画生成プロンプトを作るモード",
        "desc_pt": "Modo para criar páginas de produto Shopify, anúncios e prompts de imagem/vídeo",
        "desc_en": "Create Shopify product pages, ads, and image/video prompts",
        "icon": "🛒",
        "available": True,
    },
    "custom": {
        "id": "custom",
        "name_ja": "Custom Mode",
        "name_pt": "Modo Custom",
        "name_en": "Custom Mode",
        "desc_ja": "自由入力で任意のコンテンツを生成するモード（将来拡張用）",
        "desc_pt": "Modo de entrada livre para gerar qualquer conteúdo (para expansão futura)",
        "desc_en": "Free-input mode for generating any content (future expansion)",
        "icon": "⚙️",
        "available": True,
    },
}


def get_mode(mode_id: str) -> dict:
    return MODES.get(mode_id, MODES["commerce"])


def list_modes() -> list[dict]:
    return list(MODES.values())
