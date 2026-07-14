from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class CachePolicy:
    max_age: int | None
    immutable: bool
    public: bool
    no_store: bool


def parse_cache_control(value: str | None) -> CachePolicy:
    directives: dict[str, str | None] = {}
    for raw_part in (value or "").split(","):
        part = raw_part.strip().lower()
        if not part:
            continue
        if "=" in part:
            key, raw_value = part.split("=", 1)
            directives[key.strip()] = raw_value.strip().strip('"')
        else:
            directives[part] = None

    max_age: int | None = None
    raw_max_age = directives.get("s-maxage") or directives.get("max-age")
    if raw_max_age and raw_max_age.isdigit():
        max_age = int(raw_max_age)

    return CachePolicy(
        max_age=max_age,
        immutable="immutable" in directives,
        public="public" in directives,
        no_store="no-store" in directives,
    )


def has_version_marker(url: str) -> bool:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if any(key.lower() in {"v", "ver", "version", "hash", "rev"} for key in query):
        return True

    filename = parsed.path.rsplit("/", 1)[-1]
    stem = filename.rsplit(".", 1)[0]
    # Aceita hash hexadecimal/base36 razoavelmente longo no nome do arquivo.
    return bool(re.search(r"(?:^|[-_.])[a-z0-9]{8,}(?:$|[-_.])", stem, re.IGNORECASE))


def image_extension(url: str, content_type: str | None) -> str:
    content = (content_type or "").lower().split(";", 1)[0].strip()
    if content.startswith("image/"):
        return content.split("/", 1)[1].replace("svg+xml", "svg")
    path = urlparse(url).path
    return path.rsplit(".", 1)[-1].lower() if "." in path else ""
