from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Locator, Page, expect

from utils.config import Settings


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def from_locator(cls, locator: Locator) -> "Box":
        raw = locator.bounding_box()
        if raw is None:
            raise AssertionError("O elemento não possui bounding box; pode estar oculto.")
        return cls(**raw)

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


class LoginPage:
    def __init__(self, page: Page, settings: Settings):
        self.page = page
        self.s = settings

    @property
    def centre_button(self) -> Locator:
        return self.page.locator(self.s.sel_login_centre_button)

    @property
    def accordion(self) -> Locator:
        return self.page.locator(self.s.sel_login_accordion)

    @property
    def menu(self) -> Locator:
        return self.page.locator(self.s.sel_login_menu)

    @property
    def online_shop(self) -> Locator:
        return self.page.locator(self.s.sel_online_shop_option)

    @property
    def login_form(self) -> Locator:
        return self.page.locator(self.s.sel_login_form)

    @property
    def email_input(self) -> Locator:
        return self.page.locator(self.s.sel_email_input)

    @property
    def password_input(self) -> Locator:
        return self.page.locator(self.s.sel_password_input)

    @property
    def login_button(self) -> Locator:
        return self.page.locator(self.s.sel_login_button)

    @property
    def forgot_password(self) -> Locator:
        return self.page.locator(self.s.sel_forgot_password)

    @property
    def login_message(self) -> Locator:
        return self.page.locator(self.s.sel_login_message)

    @property
    def authenticated_marker(self) -> Locator:
        return self.page.locator(self.s.sel_authenticated_marker)

    @property
    def logout(self) -> Locator:
        return self.page.locator(self.s.sel_logout)

    def open(self) -> None:
        self.page.goto(self.s.login_url, wait_until="domcontentloaded")

    def open_login_form(self) -> None:
        expect(self.centre_button).to_be_visible()
        if not self._is_expanded(self.centre_button):
            self.centre_button.click()
        expect(self.menu).to_be_visible()
        self.online_shop.click()
        expect(self.login_form).to_be_visible()

    def login(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.login_button.click()

    def request_password_reset(self, email: str) -> None:
        self.forgot_password.click()
        input_locator = self.page.locator(self.s.sel_forgot_email_input)
        expect(input_locator).to_be_visible()
        input_locator.fill(email)
        self.page.locator(self.s.sel_forgot_submit).click()

    def reset_password(self, new_password: str) -> None:
        self.page.locator(self.s.sel_reset_password).fill(new_password)
        self.page.locator(self.s.sel_reset_password_confirm).fill(new_password)
        self.page.locator(self.s.sel_reset_submit).click()

    def css(self, locator: Locator, property_name: str, pseudo: str | None = None) -> str:
        return locator.evaluate(
            """(el, args) => {
                const [propertyName, pseudo] = args;
                return window.getComputedStyle(el, pseudo || null)
                    .getPropertyValue(propertyName)
                    .trim();
            }""",
            [property_name, pseudo],
        )

    def aria_expanded(self) -> bool:
        return self._is_expanded(self.centre_button)

    @staticmethod
    def _is_expanded(locator: Locator) -> bool:
        return (locator.get_attribute("aria-expanded") or "false").lower() == "true"

    @staticmethod
    def placeholder_is_shown(locator: Locator) -> bool:
        return bool(locator.evaluate("el => el.matches(':placeholder-shown')"))

    @staticmethod
    def normalise_css_color(value: str) -> str:
        return value.replace(" ", "").lower()

    @staticmethod
    def assert_close(actual: float, expected: float, tolerance: float, label: str) -> None:
        if abs(actual - expected) > tolerance:
            raise AssertionError(
                f"{label}: esperado {expected:.2f}±{tolerance:.2f}, obtido {actual:.2f}."
            )

    def button_style(self) -> dict[str, str]:
        return {
            "background": self.css(self.centre_button, "background-color"),
            "text": self.css(self.centre_button, "color"),
            "border": self.css(self.centre_button, "border-top-color"),
        }

    def element_text_is_bold(self, locator: Locator) -> bool:
        raw = self.css(locator, "font-weight")
        try:
            return int(raw) >= 600
        except ValueError:
            return raw.lower() in {"bold", "bolder"}

    def placeholder_style(self, locator: Locator) -> dict[str, Any]:
        weight = self.css(locator, "font-weight", "::placeholder")
        return {
            "font_family": self.css(locator, "font-family", "::placeholder"),
            "font_weight": int(weight) if weight.isdigit() else weight,
        }
