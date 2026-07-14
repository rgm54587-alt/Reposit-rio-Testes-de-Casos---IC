from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect

from pages.login_page import Box, LoginPage
from utils.config import Settings
from utils.mailbox import MailboxClient


def _canonical_color(value: str) -> tuple[int, int, int, float]:
    value = value.strip().lower().replace(" ", "")
    if value == "transparent":
        return (0, 0, 0, 0.0)
    if value.startswith("#"):
        raw = value[1:]
        if len(raw) in {3, 4}:
            raw = "".join(ch * 2 for ch in raw)
        if len(raw) == 6:
            raw += "ff"
        if len(raw) != 8:
            raise AssertionError(f"Cor hexadecimal inválida: {value!r}")
        return (
            int(raw[0:2], 16),
            int(raw[2:4], 16),
            int(raw[4:6], 16),
            round(int(raw[6:8], 16) / 255, 4),
        )
    match = re.fullmatch(r"rgba?\((\d+),(\d+),(\d+)(?:,([0-9.]+))?\)", value)
    if match:
        red, green, blue = (int(match.group(i)) for i in range(1, 4))
        alpha = float(match.group(4)) if match.group(4) is not None else 1.0
        return red, green, blue, round(alpha, 4)
    raise AssertionError(f"Formato de cor CSS não suportado: {value!r}")


def _assert_css_color(actual: str, expected: str, label: str) -> None:
    assert _canonical_color(actual) == _canonical_color(expected), (
        f"{label}: esperado {expected!r}, obtido {actual!r}."
    )


@pytest.mark.visual
def test_ct_login_001_nomenclatura_alinhamento_e_estados_visuais(
    login_page: LoginPage, settings: Settings
) -> None:
    """CT-LOGIN-001: valida Login centre, alinhamento à direita e estilos padrão/selecionado."""
    assert settings.visual_tokens_are_configured(), (
        "Configure as cores aprovadas do wireframe no arquivo .env antes de executar CT-LOGIN-001."
    )

    login_page.open()
    expect(login_page.centre_button).to_have_text("Login centre")
    expect(login_page.page.get_by_text("Login area", exact=True)).to_have_count(0)

    default_style = login_page.button_style()
    _assert_css_color(default_style["background"], settings.default_bg_color, "Fundo padrão")
    _assert_css_color(default_style["text"], settings.default_text_color, "Fonte padrão")
    _assert_css_color(default_style["border"], settings.default_border_color, "Borda padrão")

    login_page.centre_button.click()
    expect(login_page.menu).to_be_visible()
    assert login_page.aria_expanded(), "O acordeão deveria estar marcado como expandido."

    selected_style = login_page.button_style()
    _assert_css_color(selected_style["background"], settings.selected_bg_color, "Fundo selecionado")
    _assert_css_color(selected_style["text"], settings.selected_text_color, "Fonte selecionada")

    button_box = Box.from_locator(login_page.centre_button)
    accordion_box = Box.from_locator(login_page.accordion)
    LoginPage.assert_close(
        button_box.right,
        accordion_box.right,
        settings.visual_tolerance_px,
        "Alinhamento das bordas direitas",
    )


@pytest.mark.visual
def test_ct_login_002_abertura_do_acordeao_e_online_shop_em_negrito(
    login_page: LoginPage,
) -> None:
    """CT-LOGIN-002: valida abertura do menu e renomeação Shop Login -> Online Shop."""
    login_page.open()
    expect(login_page.menu).to_be_hidden()

    login_page.centre_button.click()
    expect(login_page.menu).to_be_visible()
    expect(login_page.online_shop).to_have_text("Online Shop")
    expect(login_page.page.get_by_text("Shop Login", exact=True)).to_have_count(0)
    assert login_page.element_text_is_bold(login_page.online_shop), (
        "O texto 'Online Shop' deveria estar em negrito."
    )

    login_page.online_shop.click()
    expect(login_page.login_form).to_be_visible()

    # Fecha e reabre para garantir consistência do acordeão, independentemente
    # de a seleção de Online Shop fechar o menu automaticamente.
    if not login_page.menu.is_visible():
        login_page.centre_button.click()
        expect(login_page.menu).to_be_visible()
    login_page.centre_button.click()
    expect(login_page.menu).to_be_hidden()
    login_page.centre_button.click()
    expect(login_page.menu).to_be_visible()


@pytest.mark.visual
def test_ct_login_003_campos_dimensoes_espacamento_placeholders_e_tipografia(
    login_page: LoginPage, settings: Settings
) -> None:
    """CT-LOGIN-003: valida wireframe, placeholders, dimensões, espaçamento e tipografia."""
    login_page.open()
    login_page.open_login_form()

    expect(login_page.email_input).to_have_attribute("placeholder", "e-mail address")
    expect(login_page.password_input).to_have_attribute("placeholder", "password")
    expect(login_page.login_button).to_have_text("Login")
    expect(login_page.password_input).to_have_attribute("type", "password")

    email_box = Box.from_locator(login_page.email_input)
    password_box = Box.from_locator(login_page.password_input)
    button_box = Box.from_locator(login_page.login_button)
    tolerance = settings.visual_tolerance_px

    for name, box in (("senha", password_box), ("botão", button_box)):
        LoginPage.assert_close(box.width, email_box.width, tolerance, f"Largura do {name}")
        LoginPage.assert_close(box.height, email_box.height, tolerance, f"Altura do {name}")

    reference_inputs = login_page.page.locator(settings.sel_reference_inputs)
    assert reference_inputs.count() >= 2, (
        "O componente 'Specialised databases' deve expor ao menos dois campos para a comparação de espaçamento. "
        "Ajuste SEL_REFERENCE_INPUTS no .env."
    )
    ref_first = Box.from_locator(reference_inputs.nth(0))
    ref_second = Box.from_locator(reference_inputs.nth(1))
    login_gap = password_box.y - email_box.bottom
    reference_gap = ref_second.y - ref_first.bottom
    LoginPage.assert_close(login_gap, reference_gap, tolerance, "Espaçamento vertical")

    heading_family = login_page.css(login_page.online_shop, "font-family")
    for field in (login_page.email_input, login_page.password_input):
        style = login_page.placeholder_style(field)
        normalise_font = lambda value: value.replace('"', "").replace("'", "").replace(" ", "").lower()
        assert normalise_font(style["font_family"]) == normalise_font(heading_family), (
            "A família tipográfica do placeholder deve ser igual à de 'Online Shop'."
        )
        weight = style["font_weight"]
        if isinstance(weight, int):
            is_thin = weight < 600
        else:
            is_thin = str(weight).lower() not in {"bold", "bolder", "600", "700", "800", "900"}
        assert is_thin, f"O placeholder deveria usar fonte fina, mas recebeu peso {weight}."

    assert login_page.placeholder_is_shown(login_page.email_input)
    login_page.email_input.fill("cliente.teste@example.com")
    assert not login_page.placeholder_is_shown(login_page.email_input)
    login_page.email_input.fill("")
    assert login_page.placeholder_is_shown(login_page.email_input)

    assert login_page.placeholder_is_shown(login_page.password_input)
    login_page.password_input.fill("Senha@2026")
    assert not login_page.placeholder_is_shown(login_page.password_input)
    login_page.password_input.fill("")
    assert login_page.placeholder_is_shown(login_page.password_input)


def test_ct_login_004_rejeita_credencial_invalida_e_aceita_credencial_valida(
    login_page: LoginPage, settings: Settings
) -> None:
    """CT-LOGIN-004: valida tentativa inválida e login bem-sucedido no botão Login."""
    login_page.open()
    login_page.open_login_form()

    login_page.login(settings.valid_email, settings.invalid_password)
    expect(login_page.login_message).to_be_visible()
    expect(login_page.login_message).to_contain_text(settings.invalid_login_message)
    expect(login_page.authenticated_marker).to_be_hidden()
    assert settings.invalid_password not in login_page.page.content(), (
        "A senha inválida foi exposta no HTML da página."
    )

    login_page.password_input.fill(settings.valid_password)
    login_page.login_button.click()
    expect(login_page.authenticated_marker).to_contain_text(settings.authenticated_marker_text)

    login_page.page.reload(wait_until="domcontentloaded")
    expect(login_page.authenticated_marker).to_contain_text(settings.authenticated_marker_text)
    assert settings.valid_password not in login_page.page.content(), (
        "A senha válida foi exposta no HTML da página."
    )

    if login_page.logout.count():
        login_page.logout.click()


@pytest.mark.email
def test_ct_login_005_fluxo_completo_de_forgot_password(
    login_page: LoginPage,
    settings: Settings,
    mailbox: MailboxClient,
) -> None:
    """CT-LOGIN-005: valida solicitação, e-mail, redefinição, login e não reutilização do link."""
    login_page.open()
    login_page.open_login_form()
    expect(login_page.forgot_password).to_have_text("Forgot password")

    login_page.request_password_reset(settings.recovery_email)
    forgot_message = login_page.page.locator(settings.sel_forgot_message)
    expect(forgot_message).to_be_visible()
    expect(forgot_message).to_contain_text(settings.reset_request_message)

    message = mailbox.wait_for_message(settings.recovery_email, settings.reset_email_subject)
    reset_url = message.find_link(settings.reset_link_pattern)
    login_page.page.goto(reset_url, wait_until="domcontentloaded")
    login_page.reset_password(settings.recovery_new_password)
    reset_message = login_page.page.locator(settings.sel_reset_message)
    expect(reset_message).to_be_visible()
    expect(reset_message).to_contain_text(settings.reset_success_message)

    # Senha antiga deve falhar.
    login_page.open()
    login_page.open_login_form()
    login_page.login(settings.recovery_email, settings.recovery_old_password)
    expect(login_page.login_message).to_contain_text(settings.invalid_login_message)

    # Nova senha deve autenticar.
    login_page.email_input.fill(settings.recovery_email)
    login_page.password_input.fill(settings.recovery_new_password)
    login_page.login_button.click()
    expect(login_page.authenticated_marker).to_contain_text(settings.authenticated_marker_text)

    if login_page.logout.count():
        login_page.logout.click()

    # O mesmo link não pode ser reutilizado.
    login_page.page.goto(reset_url, wait_until="domcontentloaded")
    message_locator = login_page.page.locator(settings.sel_reset_message)
    expect(message_locator).to_contain_text(settings.reset_link_expired_message)
    reset_submit = login_page.page.locator(settings.sel_reset_submit)
    if reset_submit.count():
        expect(reset_submit).to_be_disabled()
