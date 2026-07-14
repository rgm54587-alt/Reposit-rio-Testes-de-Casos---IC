from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from playwright.sync_api import Browser, Page, expect

from config import Settings
from models import Customer
from pages.checkout_page import CheckoutPage
from services.database import DatabaseClient
from services.mailbox import MailboxClient
from tests.helpers import (
    confirm_customer,
    create_pending_customer_in_new_context,
    register_pending_customer,
)


@pytest.mark.e2e
def test_ct_reg_001_existing_customer_can_login_and_access_saved_data(
    page: Page,
    checkout: CheckoutPage,
    settings: Settings,
    mailbox: MailboxClient,
    customer_factory,
    created_customers: list[str],
) -> None:
    customer: Customer = customer_factory("ct001")
    created_customers.append(customer.email)

    # Preparação autocontida: cria, confirma e autentica a conta que será usada no teste.
    register_pending_customer(page, settings, customer)
    confirm_customer(page, mailbox, customer)
    checkout.expect_checkout_login_area()
    page.context.clear_cookies()

    # Cenário principal CT-REG-001.
    checkout.open_home()
    checkout.add_first_product_and_open_checkout()
    checkout.expect_login_and_registration_options()
    checkout.choose_login()
    checkout.login(customer.email, customer.password)
    checkout.expect_logged_in()
    checkout.click_lets_go()
    checkout.expect_address_preserved(customer.address)
    checkout.expect_cart_preserved()


@pytest.mark.e2e
def test_ct_reg_002_registration_preserves_address_and_shows_correct_fields(
    checkout: CheckoutPage,
    customer_factory,
    created_customers: list[str],
) -> None:
    customer: Customer = customer_factory("ct002")
    created_customers.append(customer.email)

    checkout.open_home()
    checkout.add_first_product_and_open_checkout()
    checkout.expect_login_and_registration_options()
    checkout.click_lets_go()
    checkout.fill_address(customer.address)
    checkout.choose_register_from_address()

    checkout.expect_address_preserved(customer.address)
    checkout.expect_correct_email_label()
    expect(checkout.page.get_by_test_id("register-password")).to_be_visible()
    expect(checkout.page.get_by_test_id("register-password-repeat")).to_be_visible()

    checkout.fill_registration_credentials(customer)
    checkout.submit_registration()
    checkout.expect_address_summary(customer.address)
    checkout.expect_pending_registration_notice()


@pytest.mark.e2e
@pytest.mark.security
def test_ct_reg_003_invalid_email_and_duplicate_registration_are_blocked_safely(
    browser: Browser,
    checkout: CheckoutPage,
    settings: Settings,
    database: DatabaseClient,
    customer_factory,
    created_customers: list[str],
) -> None:
    existing: Customer = customer_factory("ct003-existing")
    created_customers.append(existing.email)
    create_pending_customer_in_new_context(browser, settings, existing)

    # Cenário A: o validador de formato intercepta um e-mail inválido no cliente.
    checkout.open_home()
    checkout.add_first_product_and_open_checkout()
    checkout.expect_login_and_registration_options()
    checkout.click_lets_go()
    checkout.fill_address(existing.address)
    checkout.choose_register_from_address()
    checkout.page.get_by_test_id("register-email").fill("carlos.pereira@")
    checkout.page.get_by_test_id("register-email").blur()
    checkout.expect_invalid_email_intercepted()

    # O formulário pode ser bloqueado pelo botão ou pela validação nativa do navegador.
    checkout.attempt_invalid_registration_submission()
    assert database.customer_by_email("carlos.pereira@") is None

    # Cenário B: erro de negócio/servidor é genérico e não enumera contas existentes.
    checkout.page.get_by_test_id("register-email").fill(existing.email)
    checkout.page.get_by_test_id("register-password").fill(existing.password)
    checkout.page.get_by_test_id("register-password-repeat").fill(existing.password)
    checkout.submit_registration()
    checkout.expect_generic_registration_error()


@pytest.mark.e2e
@pytest.mark.integration
def test_ct_reg_004_registration_is_persisted_and_confirmation_email_is_sent(
    browser: Browser,
    page: Page,
    settings: Settings,
    database: DatabaseClient,
    mailbox: MailboxClient,
    customer_factory,
    created_customers: list[str],
) -> None:
    customer: Customer = customer_factory("ct004")
    created_customers.append(customer.email)

    checkout = register_pending_customer(page, settings, customer)

    # Validação direta da pós-condição no banco de dados.
    record = database.customer_by_email(customer.email)
    assert record is not None, "O cadastro não foi persistido no banco de dados."
    assert record["email"].lower() == customer.email.lower()
    assert str(record["status"]).lower() in settings.pending_statuses
    assert record["confirmed_at"] is None
    assert record["password_hash"], "O hash da senha não foi armazenado."
    assert record["password_hash"] != customer.password, "A senha foi armazenada em texto aberto."

    # A conta pendente não pode ser usada como uma conta plenamente autenticada.
    pending_context = browser.new_context()
    pending_page = pending_context.new_page()
    try:
        pending_checkout = CheckoutPage(pending_page, settings)
        pending_checkout.open_home()
        pending_checkout.add_first_product_and_open_checkout()
        pending_checkout.choose_login()
        pending_checkout.login(customer.email, customer.password)
        pending_checkout.expect_login_rejected()
    finally:
        pending_context.close()

    # O e-mail deve informar confirmação, restrição de continuidade e usar texto padrão.
    message = mailbox.wait_for_message(customer.email)
    body = mailbox.normalized_body_text(message)
    assert settings.mail_confirmation_standard_text.lower() in body.lower()
    assert settings.mail_only_continue_text.lower() in body.lower()
    confirmation_url = mailbox.confirmation_url(message)
    assert confirmation_url.startswith(("http://", "https://"))

    # O resumo de endereço pode ser exibido, mas o avanço fica bloqueado até confirmar.
    checkout.expect_address_summary(customer.address)
    checkout.expect_pending_registration_notice()


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.retention
def test_ct_reg_005_confirmation_boundary_of_seven_days(
    browser: Browser,
    settings: Settings,
    database: DatabaseClient,
    mailbox: MailboxClient,
    customer_factory,
    created_customers: list[str],
) -> None:
    valid_customer: Customer = customer_factory("ct005-valid")
    expired_customer: Customer = customer_factory("ct005-expired")
    created_customers.extend([valid_customer.email, expired_customer.email])

    valid_context = browser.new_context()
    valid_page = valid_context.new_page()
    expired_context = browser.new_context()
    expired_page = expired_context.new_page()

    try:
        valid_checkout = register_pending_customer(valid_page, settings, valid_customer)
        expired_checkout = register_pending_customer(expired_page, settings, expired_customer)

        valid_message = mailbox.wait_for_message(valid_customer.email)
        expired_message = mailbox.wait_for_message(expired_customer.email)
        valid_url = mailbox.confirmation_url(valid_message)
        expired_url = mailbox.confirmation_url(expired_message)

        now = datetime.now(timezone.utc)

        # Dentro do prazo: 167h59min desde a criação, faltando 1 minuto para 168 horas.
        valid_created_at = now - timedelta(days=7) + timedelta(minutes=1)
        database.set_registration_window(
            valid_customer.email,
            created_at=valid_created_at,
            confirmation_expires_at=valid_created_at + timedelta(days=7),
        )

        # O mesmo contexto preserva o carrinho iniciado antes da confirmação.
        valid_page.goto(valid_url, wait_until="domcontentloaded")
        valid_checkout.expect_checkout_login_area()
        valid_checkout.login(valid_customer.email, valid_customer.password)
        valid_checkout.expect_logged_in()
        valid_checkout.expect_cart_preserved()

        valid_record = database.customer_by_email(valid_customer.email)
        assert valid_record is not None
        assert str(valid_record["status"]).lower() in settings.active_statuses
        assert valid_record["confirmed_at"] is not None

        # Fora do prazo: 168h01min desde a criação.
        expired_created_at = now - timedelta(days=7) - timedelta(minutes=1)
        database.set_registration_window(
            expired_customer.email,
            created_at=expired_created_at,
            confirmation_expires_at=expired_created_at + timedelta(days=7),
        )

        expired_page.goto(expired_url, wait_until="domcontentloaded")
        expired_checkout.expect_confirmation_expired()

        expired_record = database.customer_by_email(expired_customer.email)
        if expired_record is not None:
            assert str(expired_record["status"]).lower() not in settings.active_statuses
            assert expired_record["confirmed_at"] is None

        # Mesmo com credenciais corretas, a conta expirada não pode autenticar.
        expired_checkout.open_home()
        expired_checkout.add_first_product_and_open_checkout()
        expired_checkout.choose_login()
        expired_checkout.login(expired_customer.email, expired_customer.password)
        expired_checkout.expect_login_rejected()
    finally:
        valid_context.close()
        expired_context.close()
