"""Helpers for generated content saved in item-based formats."""

ITEM_COMPAT_KEYS = {
    "image_prompts": "image_prompt",
    "video_scripts": "video_script",
    "ads_sns_items": "ads_sns",
}


def combine_generated_items(items: dict) -> str:
    return "\n\n---\n\n".join(f"## {k}\n{v}" for k, v in items.items() if v)
