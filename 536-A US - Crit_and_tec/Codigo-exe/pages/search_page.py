from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import Locator, Page, expect


@dataclass(frozen=True)
class SearchSelectors:
    search_input: str
    search_button: str
    autocomplete_panel: str
    autocomplete_item: str
    results_container: str
    result_item: str
    no_results: str
    did_you_mean: str
    internal_type: str


class SearchPage:
    """Page Object for search and autocomplete interactions."""

    def __init__(
        self,
        page: Page,
        base_url: str,
        search_path: str,
        selectors: SearchSelectors,
    ) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.search_path = search_path if search_path.startswith("/") else f"/{search_path}"
        self.selectors = selectors

    @property
    def search_input(self) -> Locator:
        return self.page.locator(self.selectors.search_input)

    @property
    def search_button(self) -> Locator:
        return self.page.locator(self.selectors.search_button)

    @property
    def autocomplete_panel(self) -> Locator:
        return self.page.locator(self.selectors.autocomplete_panel)

    @property
    def autocomplete_items(self) -> Locator:
        return self.page.locator(self.selectors.autocomplete_item)

    @property
    def result_items(self) -> Locator:
        return self.page.locator(self.selectors.result_item)

    @property
    def no_results_message(self) -> Locator:
        return self.page.locator(self.selectors.no_results)

    @property
    def did_you_mean(self) -> Locator:
        return self.page.locator(self.selectors.did_you_mean)

    def open(self) -> None:
        self.page.goto(f"{self.base_url}{self.search_path}", wait_until="domcontentloaded")
        expect(self.search_input).to_be_visible()
        expect(self.search_input).to_be_enabled()

    def clear(self) -> None:
        self.search_input.fill("")

    def type_character(self, character: str) -> None:
        self.search_input.type(character)

    def fill(self, term: str) -> None:
        self.search_input.fill(term)

    def autocomplete_is_visible(self) -> bool:
        try:
            return self.autocomplete_panel.is_visible()
        except Exception:
            return False

    def wait_for_autocomplete(self, timeout_ms: int) -> float:
        started = monotonic()
        expect(self.autocomplete_panel).to_be_visible(timeout=timeout_ms)
        elapsed_ms = (monotonic() - started) * 1000
        return elapsed_ms

    def autocomplete_contains(self, expected_text: str) -> None:
        expect(self.autocomplete_items.filter(has_text=expected_text).first).to_be_visible()

    def submit_with_enter(self) -> None:
        self.search_input.press("Enter")
        self.wait_for_search_completion()

    def submit_with_button(self) -> None:
        expect(self.search_button).to_be_visible()
        expect(self.search_button).to_be_enabled()
        self.search_button.click()
        self.wait_for_search_completion()

    def wait_for_search_completion(self) -> None:
        # Accept either a populated result container or the explicit no-result state.
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_function(
                """
                ([resultsSelector, noResultsSelector]) => {
                    const results = document.querySelector(resultsSelector);
                    const noResults = document.querySelector(noResultsSelector);
                    return Boolean(
                        (results && results.getClientRects().length) ||
                        (noResults && noResults.getClientRects().length)
                    );
                }
                """,
                arg=[self.selectors.results_container, self.selectors.no_results],
                timeout=10_000,
            )
        except Exception:
            # The assertions that follow provide the business-facing failure.
            pass

    def visible_result_titles(self) -> list[str]:
        titles: list[str] = []
        for item in self.result_items.all():
            if item.is_visible():
                text = " ".join(item.inner_text().split())
                if text:
                    titles.append(text)
        return titles

    def assert_result_visible(self, expected_text: str) -> None:
        expect(self.result_items.filter(has_text=expected_text).first).to_be_visible()

    def assert_internal_title_not_displayed(self, forbidden_title: str) -> None:
        visible_matches = self.page.get_by_text(forbidden_title, exact=True)
        for index in range(visible_matches.count()):
            assert not visible_matches.nth(index).is_visible(), (
                f'O título interno "{forbidden_title}" foi exibido ao cliente.'
            )

    def assert_internal_type_not_displayed(self) -> None:
        if not self.selectors.internal_type.strip():
            return
        internal_records = self.page.locator(self.selectors.internal_type)
        for index in range(internal_records.count()):
            assert not internal_records.nth(index).is_visible(), (
                "Um registro interno do tipo configurado foi exibido ao cliente."
            )

    def fuzzy_search_resolves_to(
        self,
        malformed_term: str,
        expected_term: str,
        expected_product: str,
        expected_suggestion_label: str,
        submit_method: str,
    ) -> None:
        self.open()
        self.fill(malformed_term)
        if submit_method == "enter":
            self.submit_with_enter()
        elif submit_method == "button":
            self.submit_with_button()
        else:
            raise ValueError(f"Método de submissão não suportado: {submit_method}")

        direct_result = self.result_items.filter(has_text=expected_product).first
        if direct_result.is_visible():
            return

        expect(self.did_you_mean).to_be_visible()
        suggestion_text = " ".join(self.did_you_mean.inner_text().split())
        assert expected_suggestion_label.casefold() in suggestion_text.casefold(), (
            f'A sugestão "{suggestion_text}" não contém o rótulo esperado '
            f'"{expected_suggestion_label}".'
        )
        assert expected_term.casefold() in suggestion_text.casefold(), (
            f'A sugestão "{suggestion_text}" não contém o termo esperado "{expected_term}".'
        )
        self.did_you_mean.click()
        self.wait_for_search_completion()
        self.assert_result_visible(expected_product)

    def assert_no_results_message(self, expected_text: str) -> None:
        expect(self.no_results_message).to_be_visible()
        actual = " ".join(self.no_results_message.inner_text().split())
        assert expected_text.casefold() in actual.casefold(), (
            f'Mensagem esperada não encontrada. Esperado conter: "{expected_text}"; '
            f'recebido: "{actual}".'
        )

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalizes query-string ordering for Enter/button comparison."""
        parts = urlsplit(url)
        normalized_query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, normalized_query, ""))
