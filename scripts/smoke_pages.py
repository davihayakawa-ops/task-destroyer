import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

PAGES = [
    "product_input",
    "saved_data",
    "core_generation",
    "product_page",
    "image_prompt",
    "video_script",
    "ads_sns",
    "export_center",
]

BASE_PRODUCT = {
    "name": "Test Product",
    "category": "Test",
    "price": "1000",
    "description": "テスト商品です。",
    "features": "軽くて使いやすい",
    "core_source_data": {
        "name": "Test Product",
        "description": "テスト商品です。",
    },
}

BASE_CORE = (
    "## 商品の一言コンセプト\n"
    "テスト用Core\n\n"
    "## メインターゲット\n"
    "テストユーザー"
)


def run_page(page: str):
    at = AppTest.from_file(str(ROOT / "app.py"))
    at.session_state["page"] = page
    at.session_state["mode"] = "commerce"
    at.session_state["lang"] = "ja"
    at.session_state["product_id"] = "testpid"
    at.session_state["product_info"] = dict(BASE_PRODUCT)
    at.session_state["core_text"] = BASE_CORE
    at.session_state["core_status"] = "edited"
    at.session_state["generated"] = {
        "product_page": "商品ページテキスト",
        "image_prompt": "画像プロンプト",
        "video_script": "動画台本",
        "ads_sns": "SNS文",
    }
    at.run(timeout=20)
    if at.exception:
        raise AssertionError(f"{page}: {at.exception}")


def main():
    for page in PAGES:
        run_page(page)
        print(f"ok {page}")
    print("all page smoke tests ok")


if __name__ == "__main__":
    main()
