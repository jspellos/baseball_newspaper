from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ApiFetchError(RuntimeError):
    pass


def _cache_path(cache_dir: Path, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.json"


def get_json(url: str, cache_dir: Path, refresh: bool = False) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, url)

    if path.exists() and not refresh:
      return json.loads(path.read_text(encoding="utf-8"))

    request = Request(url, headers={"User-Agent": "baseball-newspaper/0.1"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ApiFetchError(f"Could not fetch MLB API URL: {url}") from exc

    path.write_text(payload, encoding="utf-8")
    return json.loads(payload)

