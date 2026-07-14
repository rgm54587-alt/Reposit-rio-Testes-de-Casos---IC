from __future__ import annotations

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from pages.detail_page import ProductDetailPage
from utils.config import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
async def browser(settings: Settings) -> Browser:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=settings.headless)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser, settings: Settings) -> BrowserContext:
    context = await browser.new_context(
        viewport={"width": settings.viewport_width, "height": settings.viewport_height},
        device_scale_factor=1,
        locale="pt-BR",
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext) -> Page:
    page = await context.new_page()
    yield page


@pytest.fixture
def detail_page(page: Page, settings: Settings) -> ProductDetailPage:
    return ProductDetailPage(page, settings)
