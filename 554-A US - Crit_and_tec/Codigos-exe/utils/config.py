from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "https://example.test").rstrip("/")
    login_path: str = os.getenv("LOGIN_PATH", "/")
    browser: str = os.getenv("BROWSER", "chromium")
    headless: bool = _bool("HEADLESS", True)
    default_timeout_ms: int = _int("DEFAULT_TIMEOUT_MS", 10000)

    valid_email: str = os.getenv("VALID_EMAIL", "cliente.teste@example.com")
    valid_password: str = os.getenv("VALID_PASSWORD", "SenhaValida@2026")
    invalid_password: str = os.getenv("INVALID_PASSWORD", "SenhaIncorreta@2026")
    authenticated_marker_text: str = os.getenv("AUTHENTICATED_MARKER_TEXT", "Minha conta")
    logout_text: str = os.getenv("LOGOUT_TEXT", "Logout")
    invalid_login_message: str = os.getenv("INVALID_LOGIN_MESSAGE", "Login inválido")

    recovery_email: str = os.getenv("RECOVERY_EMAIL", "cliente.recuperacao@example.com")
    recovery_old_password: str = os.getenv("RECOVERY_OLD_PASSWORD", "SenhaAntiga@2026")
    recovery_new_password: str = os.getenv("RECOVERY_NEW_PASSWORD", "NovaSenha@2026")
    reset_request_message: str = os.getenv("RESET_REQUEST_MESSAGE", "Solicitação enviada")
    reset_success_message: str = os.getenv("RESET_SUCCESS_MESSAGE", "Senha redefinida")
    reset_link_expired_message: str = os.getenv("RESET_LINK_EXPIRED_MESSAGE", "Link inválido")
    reset_email_subject: str = os.getenv("RESET_EMAIL_SUBJECT", "Redefinição de senha")
    reset_link_pattern: str = os.getenv("RESET_LINK_PATTERN", "/reset-password/")

    default_bg_color: str = os.getenv("DEFAULT_BG_COLOR", "__SET_FROM_WIREFRAME__")
    default_text_color: str = os.getenv("DEFAULT_TEXT_COLOR", "__SET_FROM_WIREFRAME__")
    default_border_color: str = os.getenv("DEFAULT_BORDER_COLOR", "__SET_FROM_WIREFRAME__")
    selected_bg_color: str = os.getenv("SELECTED_BG_COLOR", "__SET_FROM_WIREFRAME__")
    selected_text_color: str = os.getenv("SELECTED_TEXT_COLOR", "__SET_FROM_WIREFRAME__")
    visual_tolerance_px: float = float(os.getenv("VISUAL_TOLERANCE_PX", "2"))

    mail_backend: str = os.getenv("MAIL_BACKEND", "mailhog").lower()
    mailhog_base_url: str = os.getenv("MAILHOG_BASE_URL", "http://localhost:8025").rstrip("/")
    imap_host: str = os.getenv("IMAP_HOST", "")
    imap_port: int = _int("IMAP_PORT", 993)
    imap_username: str = os.getenv("IMAP_USERNAME", "")
    imap_password: str = os.getenv("IMAP_PASSWORD", "")
    imap_use_ssl: bool = _bool("IMAP_USE_SSL", True)
    email_wait_seconds: int = _int("EMAIL_WAIT_SECONDS", 30)

    sel_login_centre_button: str = os.getenv("SEL_LOGIN_CENTRE_BUTTON", "[data-testid='login-centre-button']")
    sel_login_accordion: str = os.getenv("SEL_LOGIN_ACCORDION", "[data-testid='login-centre-accordion']")
    sel_login_menu: str = os.getenv("SEL_LOGIN_MENU", "[data-testid='login-centre-menu']")
    sel_online_shop_option: str = os.getenv("SEL_ONLINE_SHOP_OPTION", "[data-testid='online-shop-option']")
    sel_login_form: str = os.getenv("SEL_LOGIN_FORM", "[data-testid='online-shop-login-form']")
    sel_email_input: str = os.getenv("SEL_EMAIL_INPUT", "[data-testid='login-email']")
    sel_password_input: str = os.getenv("SEL_PASSWORD_INPUT", "[data-testid='login-password']")
    sel_login_button: str = os.getenv("SEL_LOGIN_BUTTON", "[data-testid='login-submit']")
    sel_forgot_password: str = os.getenv("SEL_FORGOT_PASSWORD", "[data-testid='forgot-password-link']")
    sel_login_message: str = os.getenv("SEL_LOGIN_MESSAGE", "[data-testid='login-message']")
    sel_authenticated_marker: str = os.getenv("SEL_AUTHENTICATED_MARKER", "[data-testid='authenticated-marker']")
    sel_logout: str = os.getenv("SEL_LOGOUT", "[data-testid='logout']")
    sel_reference_specialised_databases: str = os.getenv("SEL_REFERENCE_SPECIALISED_DATABASES", "[data-testid='specialised-databases']")
    sel_reference_inputs: str = os.getenv("SEL_REFERENCE_INPUTS", "[data-testid='specialised-databases'] input")
    sel_forgot_email_input: str = os.getenv("SEL_FORGOT_EMAIL_INPUT", "[data-testid='forgot-email']")
    sel_forgot_submit: str = os.getenv("SEL_FORGOT_SUBMIT", "[data-testid='forgot-submit']")
    sel_forgot_message: str = os.getenv("SEL_FORGOT_MESSAGE", "[data-testid='forgot-message']")
    sel_reset_password: str = os.getenv("SEL_RESET_PASSWORD", "[data-testid='reset-password']")
    sel_reset_password_confirm: str = os.getenv("SEL_RESET_PASSWORD_CONFIRM", "[data-testid='reset-password-confirm']")
    sel_reset_submit: str = os.getenv("SEL_RESET_SUBMIT", "[data-testid='reset-submit']")
    sel_reset_message: str = os.getenv("SEL_RESET_MESSAGE", "[data-testid='reset-message']")

    @property
    def login_url(self) -> str:
        return f"{self.base_url}/{self.login_path.lstrip('/')}"

    def visual_tokens_are_configured(self) -> bool:
        values = (
            self.default_bg_color,
            self.default_text_color,
            self.default_border_color,
            self.selected_bg_color,
            self.selected_text_color,
        )
        return all(v and not v.startswith("__SET_") for v in values)
