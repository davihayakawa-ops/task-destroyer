import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from modules.product_input_logic import prepare_product_save_data


def test_portuguese_save_keeps_direct_core_source():
    base = {
        "name": "Produto",
        "description": "Descricao",
        "product_url": "u",
    }
    existing = {"input_ja": {"name": "古い訳"}, "translated_at": "old", "translated_by": "Davi"}

    result = prepare_product_save_data(
        base, existing, "admin", "pt", False
    )

    assert result["input_original_language"] == "pt-BR"
    assert result["translation_status"] == "not_translated"
    assert result["core_source_data"]["name"] == "Produto"
    assert result["core_source_data"]["description"] == "Descricao"
    assert result["input_ja"] == {"name": "古い訳"}


def test_admin_japanese_save_builds_core_source():
    result = prepare_product_save_data(
        {"name": "日本語名", "description": "説明"},
        {},
        "admin",
        "ja",
        False,
    )

    assert result["input_original_language"] == "ja"
    assert result["translation_status"] == "not_needed"
    assert result["core_source_data"]["name"] == "日本語名"


def test_admin_review_save_keeps_portuguese_main_fields():
    existing = {
        "input_original": {"name": "Produto", "description": "Descricao"},
        "input_ja": {"description": "古い説明"},
    }
    result = prepare_product_save_data(
        {"name": "日本語名", "description": "日本語説明"},
        existing,
        "admin",
        "ja",
        True,
    )

    assert result["name"] == "Produto"
    assert result["description"] == "Descricao"
    assert result["input_ja"]["name"] == "日本語名"
    assert result["input_ja"]["description"] == "日本語説明"
    assert result["core_source_data"]["name"] == "日本語名"


def main():
    test_portuguese_save_keeps_direct_core_source()
    test_admin_japanese_save_builds_core_source()
    test_admin_review_save_keeps_portuguese_main_fields()
    print("product input logic tests ok")


if __name__ == "__main__":
    main()
