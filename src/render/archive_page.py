from __future__ import annotations

from datetime import date
from string import Template

from src.config import STATIC_DIR, TEMPLATE_DIR


def render_archive_page(editions: list[str]) -> str:
    template = Template((TEMPLATE_DIR / "archive.html").read_text(encoding="utf-8"))
    css = (STATIC_DIR / "newspaper.css").read_text(encoding="utf-8")
    links = "\n".join(
        f'<li><a href="daily/{edition}.html">{edition}</a></li>'
        for edition in editions
    )
    return template.safe_substitute(
        css=css,
        generated_on=date.today().isoformat(),
        archive_links=links or "<li>No dated editions have been generated yet.</li>",
    )
