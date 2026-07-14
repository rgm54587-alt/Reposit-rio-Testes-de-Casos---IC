from __future__ import annotations

import os
from dataclasses import dataclass

import pytest
from dotenv import load_dotenv

from pages.search_page import SearchPage, SearchSelectors


load_dotenv()


@dataclass(frozen=True)
class TestSettings:
    base_url: str
    search_path: str
    autocomplete_term: str
    autocomplete_expected_product: str
    filter_term: str
    filter_expected_product: str
    fuzzy_expected_term: str
    fuzzy_expected_product: str
    fuzzy_spaced_input: str
    fuzzy_missing_letter_input: str
    valid_search_term: str
    valid_expected_product: str
    no_result_term: str
    did_you_mean_text: str
    no_results_text: str
    internal_title: str
    internal_type_code: str
    autocomplete_max_ms: int
    selectors: SearchSelectors


def required_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise RuntimeError(f"A variável de ambiente obrigatória {name} não foi configurada.")
    return value.strip()


@pytest.fixture(scope="session")
def settings() -> TestSettings:
    max_ms_raw = required_env("AUTOCOMPLETE_MAX_MS", "500")
    try:
        max_ms = int(max_ms_raw)
    except ValueError as exc:
        raise RuntimeError("AUTOCOMPLETE_MAX_MS deve ser um número inteiro.") from exc
    if max_ms <= 0:
        raise RuntimeError("AUTOCOMPLETE_MAX_MS deve ser maior que zero.")

    internal_type_code = required_env("INTERNAL_TYPE_CODE", "40")

    selectors = SearchSelectors(
        search_input=required_env("SEARCH_INPUT_SELECTOR", '[data-testid="search-input"]'),
        search_button=required_env("SEARCH_BUTTON_SELECTOR", '[data-testid="search-button"]'),
        autocomplete_panel=required_env(
            "AUTOCOMPLETE_PANEL_SELECTOR", '[data-testid="search-autocomplete"]'
        ),
        autocomplete_item=required_env(
            "AUTOCOMPLETE_ITEM_SELECTOR", '[data-testid="autocomplete-item"]'
        ),
        results_container=required_env(
            "SEARCH_RESULTS_CONTAINER_SELECTOR", '[data-testid="search-results"]'
        ),
        result_item=required_env(
            "SEARCH_RESULT_ITEM_SELECTOR", '[data-testid="search-result-item"]'
        ),
        no_results=required_env("NO_RESULTS_SELECTOR", '[data-testid="no-search-results"]'),
        did_you_mean=required_env("DID_YOU_MEAN_SELECTOR", '[data-testid="did-you-mean"]'),
        internal_type=os.getenv(
            "INTERNAL_TYPE_SELECTOR", f'[data-product-type="{internal_type_code}"]'
        ).strip(),
    )

    return TestSettings(
        base_url=required_env("BASE_URL"),
        search_path=required_env("SEARCH_PATH", "/"),
        autocomplete_term=required_env("AUTOCOMPLETE_TERM", "Notebook"),
        autocomplete_expected_product=required_env(
            "AUTOCOMPLETE_EXPECTED_PRODUCT", "Notebook Lenovo"
        ),
        filter_term=required_env("FILTER_TERM", "Cerveja"),
        filter_expected_product=required_env("FILTER_EXPECTED_PRODUCT", "Cerveja Premium"),
        fuzzy_expected_term=required_env("FUZZY_EXPECTED_TERM", "Chocolate"),
        fuzzy_expected_product=required_env("FUZZY_EXPECTED_PRODUCT", "Chocolate"),
        fuzzy_spaced_input=required_env("FUZZY_SPACED_INPUT", "Choco late"),
        fuzzy_missing_letter_input=required_env("FUZZY_MISSING_LETTER_INPUT", "Choclate"),
        valid_search_term=required_env("VALID_SEARCH_TERM", "Mouse Sem Fio"),
        valid_expected_product=required_env("VALID_EXPECTED_PRODUCT", "Mouse Sem Fio"),
        no_result_term=required_env("NO_RESULT_TERM", "ZXQ987ProdutoInexistente"),
        did_you_mean_text=required_env("DID_YOU_MEAN_TEXT", "Você quis dizer"),
        no_results_text=required_env("NO_RESULTS_TEXT", "Nenhum resultado encontrado"),
        internal_title=required_env("INTERNAL_TITLE", "ProductAvailability"),
        internal_type_code=internal_type_code,
        autocomplete_max_ms=max_ms,
        selectors=selectors,
    )


@pytest.fixture
def search_page(page, settings: TestSettings) -> SearchPage:
    return SearchPage(
        page=page,
        base_url=settings.base_url,
        search_path=settings.search_path,
        selectors=settings.selectors,
    )
