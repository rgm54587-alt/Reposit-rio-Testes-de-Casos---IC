from __future__ import annotations

import pytest
from playwright.sync_api import expect


pytestmark = [pytest.mark.acceptance, pytest.mark.search]


def test_ct_busca_001_autocomplete_abre_ate_o_terceiro_caractere(
    search_page, settings
) -> None:
    """CT-BUSCA-001: autocomplete appears no later than the third character."""
    search_page.open()
    search_page.clear()

    first_three = settings.autocomplete_term[:3]
    assert len(first_three) == 3, "AUTOCOMPLETE_TERM deve possuir pelo menos três caracteres."

    opened_at_character: int | None = None
    elapsed_after_trigger_ms: float | None = None

    for position, character in enumerate(first_three, start=1):
        search_page.type_character(character)
        if search_page.autocomplete_is_visible():
            opened_at_character = position
            elapsed_after_trigger_ms = 0.0
            break

        if position == 3:
            elapsed_after_trigger_ms = search_page.wait_for_autocomplete(
                timeout_ms=settings.autocomplete_max_ms
            )
            opened_at_character = 3

    assert opened_at_character is not None
    assert opened_at_character <= 3, (
        "O autocomplete não foi exibido até a digitação do terceiro caractere."
    )
    assert elapsed_after_trigger_ms is not None
    assert elapsed_after_trigger_ms <= settings.autocomplete_max_ms, (
        f"Autocomplete levou {elapsed_after_trigger_ms:.2f} ms; "
        f"limite configurado: {settings.autocomplete_max_ms} ms."
    )
    search_page.autocomplete_contains(settings.autocomplete_expected_product)


def test_ct_busca_002_nao_exibe_productavailability_tipo_40(
    search_page, settings
) -> None:
    """CT-BUSCA-002: internal ProductAvailability (40) records are not displayed."""
    search_page.open()
    search_page.fill(settings.filter_term)

    if len(settings.filter_term) >= 3:
        try:
            search_page.wait_for_autocomplete(settings.autocomplete_max_ms)
            search_page.assert_internal_title_not_displayed(settings.internal_title)
            search_page.assert_internal_type_not_displayed()
        except AssertionError:
            raise
        except Exception:
            # The final result page remains mandatory even if this UI has no autocomplete.
            pass

    search_page.submit_with_button()
    search_page.assert_result_visible(settings.filter_expected_product)
    search_page.assert_internal_title_not_displayed(settings.internal_title)
    search_page.assert_internal_type_not_displayed()


def test_ct_busca_003_busca_aproximada_corrige_espaco_e_letra_ausente(
    search_page, settings
) -> None:
    """CT-BUSCA-003: spaced and missing-letter inputs resolve directly or via suggestion."""
    search_page.fuzzy_search_resolves_to(
        malformed_term=settings.fuzzy_spaced_input,
        expected_term=settings.fuzzy_expected_term,
        expected_product=settings.fuzzy_expected_product,
        expected_suggestion_label=settings.did_you_mean_text,
        submit_method="enter",
    )

    search_page.fuzzy_search_resolves_to(
        malformed_term=settings.fuzzy_missing_letter_input,
        expected_term=settings.fuzzy_expected_term,
        expected_product=settings.fuzzy_expected_product,
        expected_suggestion_label=settings.did_you_mean_text,
        submit_method="button",
    )


def test_ct_busca_004_campo_vazio_executa_busca_curinga_com_enter_e_lupa(
    search_page,
) -> None:
    """CT-BUSCA-004: blank input behaves as wildcard search for both submission methods."""
    search_page.open()
    search_page.clear()
    search_page.submit_with_button()
    button_results = search_page.visible_result_titles()

    assert button_results, (
        "A pesquisa vazia pela lupa não retornou produtos pesquisáveis como busca curinga."
    )
    search_page.assert_internal_type_not_displayed()

    search_page.open()
    search_page.clear()
    search_page.submit_with_enter()
    enter_results = search_page.visible_result_titles()

    assert enter_results, (
        "A pesquisa vazia com Enter não retornou produtos pesquisáveis como busca curinga."
    )
    search_page.assert_internal_type_not_displayed()

    assert enter_results == button_results, (
        "Enter e lupa retornaram listas diferentes para a pesquisa curinga vazia. "
        f"Lupa: {button_results}; Enter: {enter_results}."
    )


def test_ct_busca_005_enter_equivale_a_lupa_e_exibe_mensagem_sem_resultado(
    search_page, settings
) -> None:
    """CT-BUSCA-005: Enter/button parity and explicit no-result feedback."""
    search_page.open()
    search_page.fill(settings.valid_search_term)
    search_page.submit_with_enter()
    enter_url = search_page.normalize_url(search_page.page.url)
    enter_results = search_page.visible_result_titles()
    search_page.assert_result_visible(settings.valid_expected_product)

    search_page.open()
    search_page.fill(settings.valid_search_term)
    search_page.submit_with_button()
    button_url = search_page.normalize_url(search_page.page.url)
    button_results = search_page.visible_result_titles()
    search_page.assert_result_visible(settings.valid_expected_product)

    assert enter_url == button_url, (
        f"Enter e lupa navegaram para URLs diferentes: {enter_url!r} != {button_url!r}."
    )
    assert enter_results == button_results, (
        "Enter e lupa retornaram resultados ou ordenações diferentes. "
        f"Enter: {enter_results}; Lupa: {button_results}."
    )

    search_page.open()
    search_page.fill(settings.no_result_term)
    search_page.submit_with_enter()
    assert search_page.visible_result_titles() == [], (
        "A busca inexistente apresentou produtos como correspondências válidas."
    )
    search_page.assert_no_results_message(settings.no_results_text)

    search_page.open()
    search_page.fill(settings.no_result_term)
    search_page.submit_with_button()
    assert search_page.visible_result_titles() == [], (
        "A busca inexistente pela lupa apresentou produtos como correspondências válidas."
    )
    search_page.assert_no_results_message(settings.no_results_text)
