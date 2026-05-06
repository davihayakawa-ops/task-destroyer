"""Product input save helpers.

These helpers keep the Portuguese original, Japanese review data, and Core
source data rules in one place so the Streamlit page can stay focused on UI.
"""

PREP_FIELDS = (
    "product_prep_status",
    "product_prep_approved",
    "product_prep_approved_by",
    "product_prep_approved_at",
    "product_prep_review_note",
    "product_prep_submitted_by",
    "product_prep_submitted_at",
)

PRODUCT_TRANSLATABLE_FIELDS = (
    "name",
    "description",
    "price",
    "category",
    "target",
    "use_scenes",
    "notes",
    "competitor_urls",
    "weaknesses",
    "features",
    "product_prep_review_note",
    "age",
    "gender",
    "prohibited",
    "brand_tone",
)

CORE_SOURCE_FIELDS = (
    "name",
    "category",
    "price",
    "target",
    "gender",
    "age",
    "product_url",
    "features",
    "weaknesses",
    "brand_tone",
    "prohibited",
    "description",
    "use_scenes",
    "competitor_urls",
    "notes",
    "assignee",
    "final_reviewer",
)

TRANSLATION_META_FIELDS = ("input_ja", "translated_at", "translated_by")

PRODUCT_FIELD_LABELS_JA = {
    "name": "商品名",
    "description": "商品説明",
    "price": "価格メモ",
    "category": "カテゴリ",
    "target": "ターゲット",
    "use_scenes": "使用シーン",
    "notes": "商品メモ",
    "competitor_urls": "競合URLメモ",
    "weaknesses": "競合分析メモ",
    "features": "差別化ポイント",
    "product_prep_review_note": "差し戻しコメント",
    "age": "年齢層",
    "gender": "性別",
    "prohibited": "禁止表現",
    "brand_tone": "ブランドトーン",
    "product_url": "商品URL",
    "assignee": "担当者",
    "final_reviewer": "最終確認者",
}

PRODUCT_PREP_STATUS_LABELS = {
    "draft": ("📝 下書き", "📝 Rascunho"),
    "waiting_review": ("⏳ Davi確認待ち", "⏳ Aguardando revisão"),
    "approved": ("✅ 承認済み", "✅ Aprovado"),
    "rejected": ("❌ 差し戻し", "❌ Recusado"),
}


def product_prep_status_label(status: str) -> tuple:
    return PRODUCT_PREP_STATUS_LABELS.get(
        status, PRODUCT_PREP_STATUS_LABELS["draft"]
    )


def _copy_translation_meta(target: dict, existing: dict):
    for key in TRANSLATION_META_FIELDS:
        target[key] = existing.get(key, {} if key == "input_ja" else "")


def prepare_product_save_data(
    new_info: dict,
    existing: dict,
    role: str,
    save_lang: str,
    save_in_ja_review: bool,
) -> dict:
    """Return product data with prep and translation metadata applied."""
    data = dict(new_info)
    existing = existing or {}

    for key in PREP_FIELDS:
        if key in existing:
            data[key] = existing[key]

    if role == "product_researcher":
        # Researcher always saves in Portuguese; Japanese review data is created later.
        data["input_original"] = {
            k: data.get(k, "") for k in PRODUCT_TRANSLATABLE_FIELDS
        }
        data["input_original_language"] = "pt-BR"
        data["translation_status"] = "not_translated"
        data["core_source_data"] = {}
        _copy_translation_meta(data, existing)
        return data

    if save_in_ja_review:
        # Admin is editing Japanese review data. Keep the Portuguese main fields intact.
        new_ja_vals = {
            k: data.get(k, "") for k in PRODUCT_TRANSLATABLE_FIELDS if data.get(k)
        }
        updated_ja = {**(existing.get("input_ja") or {}), **new_ja_vals}
        original = existing.get("input_original") or {}

        for key in PRODUCT_TRANSLATABLE_FIELDS:
            data[key] = original.get(key, existing.get(key, ""))

        data["input_original"] = (
            original if original else {
                k: data.get(k, "") for k in PRODUCT_TRANSLATABLE_FIELDS
            }
        )
        data["input_original_language"] = "pt-BR"
        data["input_ja"] = updated_ja
        data["translation_status"] = "translated"

        core_source = {k: data.get(k, "") for k in CORE_SOURCE_FIELDS}
        core_source.update({
            k: v for k, v in updated_ja.items() if k in CORE_SOURCE_FIELDS and v
        })
        data["core_source_data"] = core_source
        for key in ("translated_at", "translated_by"):
            data[key] = existing.get(key, "")
        return data

    if save_lang == "ja":
        # Admin entered Japanese directly; Core can use it without translation.
        data["input_original"] = {
            k: data.get(k, "") for k in PRODUCT_TRANSLATABLE_FIELDS
        }
        data["input_original_language"] = "ja"
        data["translation_status"] = "not_needed"
        data["core_source_data"] = {
            k: data.get(k, "") for k in CORE_SOURCE_FIELDS
        }
        _copy_translation_meta(data, existing)
        return data

    # Admin entered Portuguese; keep any existing Japanese review data until retranslated.
    data["input_original"] = {
        k: data.get(k, "") for k in PRODUCT_TRANSLATABLE_FIELDS
    }
    data["input_original_language"] = "pt-BR"
    data["translation_status"] = existing.get("translation_status", "not_translated")
    data["core_source_data"] = existing.get("core_source_data", {})
    _copy_translation_meta(data, existing)
    return data
