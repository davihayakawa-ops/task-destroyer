import json
from datetime import datetime


class Exporter:
    @staticmethod
    def to_markdown(title: str, content: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"# {title}\n\n生成日時: {timestamp}\n\n---\n\n{content}"

    @staticmethod
    def to_json(data: dict) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)

    @staticmethod
    def core_to_markdown(core_text: str, product_name: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"# Core / 核 - {product_name}\n\n生成日時: {timestamp}\n\n---\n\n{core_text}"

    @staticmethod
    def product_page_to_html(content: str, product_name: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{product_name}</title>
</head>
<body>
<div class="product-content">
{content.replace(chr(10), '<br>')}
</div>
</body>
</html>"""

    @staticmethod
    def pack_to_markdown(pack_name: str, contents: dict) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"# {pack_name}\n\n生成日時: {timestamp}\n\n---\n"]
        for key, value in contents.items():
            lines.append(f"\n## {key}\n\n{value}\n")
        return "\n".join(lines)
