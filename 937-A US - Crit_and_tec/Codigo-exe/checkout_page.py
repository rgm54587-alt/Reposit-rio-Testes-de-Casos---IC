from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from config import Settings
from models import Address, Customer


class CheckoutPage:
    """Page Object baseado em data-testid para reduzir seletores frágeis.

    Ajuste os atributos data-testid da aplicação real ou adapte somente esta classe.
    """

    def __init__(self, page: Page, settings: Settings):
        self.page = page
        self.settings = settings

    def open_home(self) -> None:
        self.page.goto(self.settings.base_url, wait_until="domcontentloaded")

    def add_first_product_and_open_checkout(self) -> None:
        self.page.get_by_test_id("add-to-cart").first.click()
        self.page.get_by_test_id("open-cart").click()
        expect(self.page.get_by_test_id("cart-item").first).to_be_visible()
        self.page.get_by_test_id("checkout").click()

    def expect_login_and_registration_options(self) -> None:
        expect(self.page.get_by_test_id("login-option")).to_be_visible()
        expect(self.page.get_by_test_id("register-option")).to_be_visible()

    def click_lets_go(self) -> None:
        self.page.get_by_test_id("lets-go").click()
        expect(self.page.get_by_test_id("checkout-address")).to_be_visible()

    def choose_login(self) -> None:
        self.page.get_by_test_id("login-option").click()
        expect(self.page.get_by_test_id("login-form")).to_be_visible()

    def login(self, email: str, password: str) -> None:
        self.page.get_by_test_id("login-email").fill(email)
        self.page.get_by_test_id("login-password").fill(password)
        self.page.get_by_test_id("login-submit").click()

    def expect_logged_in(self) -> None:
        expect(self.page.get_by_test_id("customer-data")).to_be_visible()

    def expect_login_rejected(self) -> None:
        expect(self.page.get_by_test_id("customer-data")).not_to_be_visible()
        feedback = self.page.locator(
            "[data-testid='login-error'], "
            "[data-testid='registration-pending-message']"
        ).first
        expect(feedback).to_be_visible()

    def fill_address(self, address: Address) -> None:
        values = {
            "first-name": address.first_name,
            "last-name": address.last_name,
            "phone": address.phone,
            "postal-code": address.postal_code,
            "street": address.street,
            "number": address.number,
            "complement": address.complement,
            "district": address.district,
            "city": address.city,
            "state": address.state,
            "country": address.country,
        }
        for test_id, value in values.items():
            self.page.get_by_test_id(test_id).fill(value)

    def expect_address_preserved(self, address: Address) -> None:
        values = {
            "first-name": address.first_name,
            "last-name": address.last_name,
            "phone": address.phone,
            "postal-code": address.postal_code,
            "street": address.street,
            "number": address.number,
            "complement": address.complement,
            "district": address.district,
            "city": address.city,
            "state": address.state,
            "country": address.country,
        }
        for test_id, value in values.items():
            expect(self.page.get_by_test_id(test_id)).to_have_value(value)

    def choose_register_from_address(self) -> None:
        self.page.get_by_test_id("register-from-address").click()
        expect(self.page.get_by_test_id("registration-form")).to_be_visible()
        expect(self.page.get_by_test_id("register-password")).to_be_visible()
        expect(self.page.get_by_test_id("register-password-repeat")).to_be_visible()

    def expect_correct_email_label(self) -> None:
        label = self.page.get_by_test_id("register-email-label")
        expect(label).to_have_text(re.compile(r"^\s*e-?mail\s*:?\s*$", re.IGNORECASE))
        assert "patternlab" not in label.inner_text().lower(), (
            "O rótulo técnico 'patternlab' foi exposto ao usuário."
        )

    def fill_registration_credentials(self, customer: Customer) -> None:
        self.page.get_by_test_id("register-email").fill(customer.email)
        self.page.get_by_test_id("register-password").fill(customer.password)
        self.page.get_by_test_id("register-password-repeat").fill(customer.password)

    def submit_registration(self) -> None:
        self.page.get_by_test_id("register-submit").click()

    def attempt_invalid_registration_submission(self) -> None:
        submit = self.page.get_by_test_id("register-submit")
        if submit.is_enabled():
            submit.click()
        expect(self.page.get_by_test_id("registration-form")).to_be_visible()

    def register_customer(self, customer: Customer) -> None:
        self.open_home()
        self.add_first_product_and_open_checkout()
        self.expect_login_and_registration_options()
        self.click_lets_go()
        self.fill_address(customer.address)
        self.choose_register_from_address()
        self.expect_address_preserved(customer.address)
        self.fill_registration_credentials(customer)
        self.submit_registration()

    def expect_address_summary(self, address: Address) -> None:
        summary = self.page.get_by_test_id("address-summary")
        expect(summary).to_be_visible()
        for value in (
            address.first_name,
            address.last_name,
            address.postal_code,
            address.street,
            address.number,
            address.city,
            address.state,
            address.country,
        ):
            expect(summary).to_contain_text(value)

    def expect_pending_registration_notice(self) -> None:
        expect(self.page.get_by_test_id("registration-pending-message")).to_contain_text(
            self.settings.registration_pending_text
        )

    def expect_invalid_email_intercepted(self) -> None:
        email_input = self.page.get_by_test_id("register-email")
        expect(email_input).to_have_attribute("aria-invalid", "true")
        expect(self.page.get_by_test_id("register-email-error")).to_be_visible()

    def expect_generic_registration_error(self) -> None:
        error = self.page.get_by_test_id("registration-error")
        expect(error).to_have_text(self.settings.registration_generic_error)
        normalized = error.inner_text().lower()
        forbidden_details = (
            "already registered",
            "already exists",
            "e-mail already",
            "email already",
            "password field",
            "database",
            "sql",
            "constraint",
        )
        assert not any(token in normalized for token in forbidden_details), (
            "A mensagem de erro revelou detalhes sensíveis: " + normalized
        )

    def expect_confirmation_expired(self) -> None:
        expect(self.page.get_by_test_id("registration-expired-message")).to_contain_text(
            self.settings.registration_expired_text
        )
        expect(self.page.get_by_test_id("customer-data")).not_to_be_visible()

    def expect_checkout_login_area(self) -> None:
        expect(self.page).to_have_url(re.compile(self.settings.checkout_login_url_pattern))
        expect(self.page.get_by_test_id("login-form")).to_be_visible()

    def expect_cart_preserved(self) -> None:
        cart_item = self.page.locator(
            "[data-testid='cart-item'], [data-testid='checkout-cart-item']"
        ).first
        expect(cart_item).to_be_visible()
