from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from playwright.async_api import Locator, Page, Response, expect

from utils.config import Settings


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass(frozen=True)
class CoverResponse:
    url: str
    status: int
    headers: dict[str, str]
    body_size: int
    from_service_worker: bool


@dataclass(frozen=True)
class CacheReuseObservation:
    url: str
    served_from_cache: bool
    from_disk_cache: bool
    from_service_worker: bool
    encoded_data_length: float | None


class ProductDetailPage:
    def __init__(self, page: Page, settings: Settings):
        self.page = page
        self.settings = settings

    @property
    def container(self) -> Locator:
        return self.page.locator(self.settings.detail_container_selector)

    @property
    def title(self) -> Locator:
        return self.page.locator(self.settings.title_selector)

    @property
    def author(self) -> Locator:
        return self.page.locator(self.settings.author_selector)

    @property
    def cover(self) -> Locator:
        return self.page.locator(self.settings.cover_selector)

    @property
    def bibliographic_rows(self) -> Locator:
        return self.page.locator(self.settings.bibliographic_row_selector)

    async def open(self, product_id: str) -> None:
        await self.page.goto(self.settings.detail_url(product_id), wait_until="domcontentloaded")
        await expect(self.container).to_be_visible()
        await expect(self.cover).to_be_visible()
        await self.wait_for_cover_loaded()

    async def wait_for_cover_loaded(self) -> None:
        await self.cover.evaluate(
            """img => new Promise((resolve, reject) => {
                if (img.complete && img.naturalWidth > 0) return resolve(true);
                const timer = setTimeout(() => reject(new Error('Timeout loading cover')), 10000);
                img.addEventListener('load', () => { clearTimeout(timer); resolve(true); }, {once: true});
                img.addEventListener('error', () => { clearTimeout(timer); reject(new Error('Cover failed')); }, {once: true});
            })"""
        )

    async def rect(self, locator: Locator) -> Rect:
        box = await locator.bounding_box()
        if box is None:
            raise AssertionError("Elemento esperado não possui área renderizada.")
        return Rect(**box)

    async def cover_rect(self) -> Rect:
        return await self.rect(self.cover)

    async def relative_cover_rect(self) -> Rect:
        cover = await self.cover_rect()
        container = await self.rect(self.container)
        return Rect(
            x=cover.x - container.x,
            y=cover.y - container.y,
            width=cover.width,
            height=cover.height,
        )

    async def image_metadata(self) -> dict[str, Any]:
        return await self.cover.evaluate(
            """img => ({
                src: img.currentSrc || img.src,
                alt: img.getAttribute('alt') || '',
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                renderedWidth: img.getBoundingClientRect().width,
                renderedHeight: img.getBoundingClientRect().height,
                complete: img.complete
            })"""
        )

    async def bibliographic_line_count(self) -> int:
        return await self.bibliographic_rows.count()

    async def open_and_collect_layout_samples(self, product_id: str, duration_ms: int) -> list[Rect]:
        selector = json.dumps(self.settings.cover_selector)
        monitor_script = f"""
            (() => {{
                window.__coverPositionSamples = [];
                const selector = {selector};
                let stopped = false;
                const sample = () => {{
                    if (stopped) return;
                    const element = document.querySelector(selector);
                    if (element) {{
                        const rect = element.getBoundingClientRect();
                        window.__coverPositionSamples.push({{
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            time: performance.now()
                        }});
                        if (window.__coverPositionSamples.length > 500) {{
                            window.__coverPositionSamples.shift();
                        }}
                    }}
                    requestAnimationFrame(sample);
                }};
                requestAnimationFrame(sample);
                window.__stopCoverPositionMonitor = () => {{ stopped = true; }};
            }})();
        """
        await self.page.add_init_script(script=monitor_script)
        await self.page.goto(self.settings.detail_url(product_id), wait_until="domcontentloaded")
        await expect(self.container).to_be_visible()
        await expect(self.cover).to_be_visible()
        await self.wait_for_cover_loaded()
        await self.page.wait_for_timeout(duration_ms)
        await self.page.evaluate("window.__stopCoverPositionMonitor?.()")
        raw_samples = await self.page.evaluate("window.__coverPositionSamples || []")
        return [
            Rect(
                x=float(item["x"]),
                y=float(item["y"]),
                width=float(item["width"]),
                height=float(item["height"]),
            )
            for item in raw_samples
        ]


    async def observe_cover_cache_on_reload(self, expected_url: str) -> CacheReuseObservation:
        session = await self.page.context.new_cdp_session(self.page)
        cached_request_ids: set[str] = set()
        responses: dict[str, dict[str, Any]] = {}
        encoded_lengths: dict[str, float] = {}

        def on_served_from_cache(event: dict[str, Any]) -> None:
            request_id = event.get("requestId")
            if request_id:
                cached_request_ids.add(str(request_id))

        def on_response(event: dict[str, Any]) -> None:
            request_id = event.get("requestId")
            response = event.get("response")
            if request_id and isinstance(response, dict):
                responses[str(request_id)] = response

        def on_finished(event: dict[str, Any]) -> None:
            request_id = event.get("requestId")
            if request_id:
                encoded_lengths[str(request_id)] = float(event.get("encodedDataLength", 0.0))

        session.on("Network.requestServedFromCache", on_served_from_cache)
        session.on("Network.responseReceived", on_response)
        session.on("Network.loadingFinished", on_finished)
        try:
            await session.send("Network.enable")
            await self.page.reload(wait_until="networkidle")
            await self.wait_for_cover_loaded()

            matching = [
                (request_id, response)
                for request_id, response in responses.items()
                if response.get("url") == expected_url
            ]
            if not matching:
                raise AssertionError(
                    "A recarga não produziu telemetria de rede para a URL da capa. "
                    "Verifique se o recurso permanece no mesmo endereço e se é carregado pelo navegador."
                )

            request_id, response = matching[-1]
            from_disk = bool(response.get("fromDiskCache", False))
            from_service_worker = bool(response.get("fromServiceWorker", False))
            served = request_id in cached_request_ids or from_disk or from_service_worker
            return CacheReuseObservation(
                url=expected_url,
                served_from_cache=served,
                from_disk_cache=from_disk,
                from_service_worker=from_service_worker,
                encoded_data_length=encoded_lengths.get(request_id),
            )
        finally:
            await session.detach()

    async def capture_cover_response(self, product_id: str) -> CoverResponse:
        image_responses: list[Response] = []

        def handle_response(response: Response) -> None:
            if response.request.resource_type == "image":
                image_responses.append(response)

        self.page.on("response", handle_response)
        try:
            await self.page.goto(self.settings.detail_url(product_id), wait_until="networkidle")
            await expect(self.cover).to_be_visible()
            await self.wait_for_cover_loaded()
            metadata = await self.image_metadata()
            src = str(metadata["src"])

            matching = [response for response in image_responses if response.url == src]
            if not matching:
                raise AssertionError(
                    "Não foi possível associar a resposta HTTP capturada à URL atual da capa. "
                    "Verifique se a imagem é carregada por HTTP e não por data URL/blob."
                )
            cover_response = matching[-1]

            headers = await cover_response.all_headers()
            try:
                body_size = len(await cover_response.body())
            except Exception:
                body_size = int(headers.get("content-length", "0") or 0)

            return CoverResponse(
                url=cover_response.url,
                status=cover_response.status,
                headers=headers,
                body_size=body_size,
                from_service_worker=cover_response.from_service_worker,
            )
        finally:
            self.page.remove_listener("response", handle_response)
