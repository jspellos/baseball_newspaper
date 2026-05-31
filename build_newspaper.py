from __future__ import annotations

import argparse
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from src.config import OUTPUT_DIR
from src.data.mlb_api import MlbApi
from src.data.normalize import normalize_bundle, sample_newspaper
from src.render.archive_page import render_archive_page
from src.render.daily_page import render_daily_page


DATED_EDITION = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a daily MLB newspaper page.")
    parser.add_argument("--date", default=yesterday(), help="Game date in YYYY-MM-DD format.")
    parser.add_argument("--sample", action="store_true", help="Render with bundled sample data.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignore cached API responses.")
    parser.add_argument("--out", help="Optional output HTML path.")
    return parser.parse_args()


def validate_date(value: str) -> str:
    datetime.strptime(value, "%Y-%m-%d")
    return value


def output_path(args: argparse.Namespace) -> Path:
    if args.out:
        return Path(args.out)
    if args.sample:
        return OUTPUT_DIR / "daily" / "sample.html"
    return OUTPUT_DIR / "daily" / f"{args.date}.html"


def dated_editions() -> list[str]:
    daily_dir = OUTPUT_DIR / "daily"
    if not daily_dir.exists():
        return []
    return sorted(
        path.stem
        for path in daily_dir.glob("*.html")
        if DATED_EDITION.fullmatch(path.stem)
    )


def edition_links(edition: str, editions: list[str]) -> str:
    links = []
    if edition in editions:
        index = editions.index(edition)
        if index > 0:
            previous = editions[index - 1]
            links.append(f'<a href="{previous}.html">&larr; {previous}</a>')
        links.append('<a href="../archive.html">Archive</a>')
        links.append('<a href="../index.html">Latest</a>')
        if index + 1 < len(editions):
            next_edition = editions[index + 1]
            links.append(f'<a href="{next_edition}.html">{next_edition} &rarr;</a>')
    return " | ".join(links)


def update_archive_and_latest(editions: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    archive = render_archive_page(list(reversed(editions)))
    (OUTPUT_DIR / "archive.html").write_text(archive, encoding="utf-8")
    if editions:
        latest = f"daily/{editions[-1]}.html"
        redirect = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url={latest}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Baseball Daily</title>
</head>
<body>
  <p>Opening the <a href="{latest}">latest Baseball Daily edition</a>.</p>
</body>
</html>
"""
        (OUTPUT_DIR / "index.html").write_text(redirect, encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.date = validate_date(args.date)

    if args.sample:
        newspaper = sample_newspaper()
    else:
        api = MlbApi(refresh_cache=args.refresh_cache)
        newspaper = normalize_bundle(api.daily_bundle(args.date))

    path = output_path(args)
    path.parent.mkdir(parents=True, exist_ok=True)
    editions = dated_editions()
    if not args.sample and args.date not in editions:
        editions.append(args.date)
        editions.sort()
    html = render_daily_page(newspaper, edition_links(args.date, editions))
    path.write_text(html, encoding="utf-8")
    if not args.sample:
        update_archive_and_latest(editions)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
