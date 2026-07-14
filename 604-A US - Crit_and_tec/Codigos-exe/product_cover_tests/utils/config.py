from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _get_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "http://localhost:3000").rstrip("/")
    detail_path_template: str = os.getenv("DETAIL_PATH_TEMPLATE", "/products/{product_id}")

    title_main_id: str = os.getenv("TITLE_MAIN_ID", "TITULO-001")
    title_main_name: str = os.getenv("TITLE_MAIN_NAME", "Dom Casmurro")
    title_main_author: str = os.getenv("TITLE_MAIN_AUTHOR", "Machado de Assis")
    title_main_cover_token: str = os.getenv("TITLE_MAIN_COVER_TOKEN", "dom-casmurro")
    title_other_id: str = os.getenv("TITLE_OTHER_ID", "TITULO-002")
    title_other_name: str = os.getenv("TITLE_OTHER_NAME", "Memórias Póstumas de Brás Cubas")
    title_other_cover_token: str = os.getenv("TITLE_OTHER_COVER_TOKEN", "memorias-postumas")
    title_third_id: str = os.getenv("TITLE_THIRD_ID", "TITULO-003")
    title_third_name: str = os.getenv("TITLE_THIRD_NAME", "Grande Sertão: Veredas")

    title_few_bib_id: str = os.getenv("TITLE_FEW_BIB_ID", "TITULO-RESUMIDO")
    title_many_bib_id: str = os.getenv("TITLE_MANY_BIB_ID", "TITULO-COMPLETO")
    expected_few_bib_lines: int = _get_int("EXPECTED_FEW_BIB_LINES", 3)
    expected_many_bib_lines: int = _get_int("EXPECTED_MANY_BIB_LINES", 12)

    detail_container_selector: str = os.getenv(
        "DETAIL_CONTAINER_SELECTOR", '[data-testid="product-detail"]'
    )
    title_selector: str = os.getenv("TITLE_SELECTOR", '[data-testid="product-title"]')
    author_selector: str = os.getenv("AUTHOR_SELECTOR", '[data-testid="product-author"]')
    cover_selector: str = os.getenv("COVER_SELECTOR", '[data-testid="product-cover"] img')
    bibliographic_row_selector: str = os.getenv(
        "BIBLIOGRAPHIC_ROW_SELECTOR", '[data-testid="bibliographic-row"]'
    )

    viewport_width: int = _get_int("VIEWPORT_WIDTH", 1440)
    viewport_height: int = _get_int("VIEWPORT_HEIGHT", 1000)
    expected_cover_width_px: float = _get_float("EXPECTED_COVER_WIDTH_PX", 240)
    expected_cover_height_px: float = _get_float("EXPECTED_COVER_HEIGHT_PX", 360)
    expected_cover_x_relative_px: float = _get_float("EXPECTED_COVER_X_RELATIVE_PX", 48)
    expected_cover_y_relative_px: float = _get_float("EXPECTED_COVER_Y_RELATIVE_PX", 40)
    geometry_tolerance_px: float = _get_float("GEOMETRY_TOLERANCE_PX", 3)
    aspect_ratio_tolerance: float = _get_float("ASPECT_RATIO_TOLERANCE", 0.02)
    max_layout_shift_px: float = _get_float("MAX_LAYOUT_SHIFT_PX", 3)
    layout_monitor_ms: int = _get_int("LAYOUT_MONITOR_MS", 2500)

    max_image_scale_factor: float = _get_float("MAX_IMAGE_SCALE_FACTOR", 2.0)
    min_image_scale_factor: float = _get_float("MIN_IMAGE_SCALE_FACTOR", 1.0)
    max_image_bytes: int = _get_int("MAX_IMAGE_BYTES", 350000)
    allowed_image_formats: tuple[str, ...] = tuple(
        item.strip().lower()
        for item in os.getenv("ALLOWED_IMAGE_FORMATS", "webp,avif,jpeg,jpg,png").split(",")
        if item.strip()
    )

    min_cache_max_age_seconds: int = _get_int("MIN_CACHE_MAX_AGE_SECONDS", 31536000)
    require_immutable_cache: bool = _get_bool("REQUIRE_IMMUTABLE_CACHE", True)
    require_versioned_image_url: bool = _get_bool("REQUIRE_VERSIONED_IMAGE_URL", True)
    require_cover_alt_text: bool = _get_bool("REQUIRE_COVER_ALT_TEXT", True)
    headless: bool = _get_bool("HEADLESS", True)

    def detail_url(self, product_id: str) -> str:
        return f"{self.base_url}{self.detail_path_template.format(product_id=product_id)}"
