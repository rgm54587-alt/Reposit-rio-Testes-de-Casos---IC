from __future__ import annotations

import pytest
from playwright.sync_api import Browser, Playwright

from pages.login_page import LoginPage
from utils.config import Settings
from utils.mailbox import MailboxClient


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def browser(playwright: Playwright, settings: Settings) -> Browser:
    browser_type = getattr(playwright, settings.browser)
    browser = browser_type.launch(headless=settings.headless)
    yield browser
    browser.close()


@pytest.fixture()
def login_page(browser: Browser, settings: Settings) -> LoginPage:
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(settings.default_timeout_ms)
    login = LoginPage(page, settings)
    yield login
    context.close()


@pytest.fixture(scope="session")
def mailbox(settings: Settings) -> MailboxClient:
    return MailboxClient(settings)
