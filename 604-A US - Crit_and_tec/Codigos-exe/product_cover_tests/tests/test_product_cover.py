from __future__ import annotations

import math

import pytest
from playwright.async_api import expect

from pages.detail_page import ProductDetailPage, Rect
from utils.config import Settings
from utils.http_cache import has_version_marker, image_extension, parse_cache_control


def assert_close(actual: float, expected: float, tolerance: float, label: str) -> None:
    assert abs(actual - expected) <= tolerance, (
        f"{label}: esperado {expected:.2f} ± {tolerance:.2f}, obtido {actual:.2f}."
    )


def max_position_delta(samples: list[Rect]) -> float:
    if not samples:
        raise AssertionError("Nenhuma amostra da posição da capa foi coletada.")
    xs = [sample.x for sample in samples]
    ys = [sample.y for sample in samples]
    return max(max(xs) - min(xs), max(ys) - min(ys))


@pytest.mark.asyncio
async def test_ct_capa_001_exibe_capa_correspondente_ao_titulo(
    detail_page: ProductDetailPage,
    settings: Settings,
) -> None:
    await detail_page.open(settings.title_main_id)

    await expect(detail_page.title).to_contain_text(settings.title_main_name)
    await expect(detail_page.author).to_contain_text(settings.title_main_author)

    metadata = await detail_page.image_metadata()
    src = str(metadata["src"]).lower()
    alt = str(metadata["alt"]).strip().lower()

    assert metadata["complete"] is True
    assert metadata["naturalWidth"] > 0 and metadata["naturalHeight"] > 0
    assert settings.title_main_cover_token.lower() in src, (
        "A URL da capa não contém o identificador esperado do título. "
        "Adapte TITLE_MAIN_COVER_TOKEN para o padrão real da aplicação."
    )
    assert settings.title_other_cover_token.lower() not in src, (
        "A página exibiu indício da capa pertencente a outro produto."
    )

    if settings.require_cover_alt_text:
        assert alt, "A imagem de capa não possui texto alternativo."
        assert (
            settings.title_main_name.lower() in alt
            or "capa" in alt
            or settings.title_main_author.lower() in alt
        ), "O texto alternativo não identifica adequadamente a capa ou o título."

    first_src = src
    await detail_page.page.reload(wait_until="networkidle")
    await detail_page.wait_for_cover_loaded()
    refreshed_src = str((await detail_page.image_metadata())["src"]).lower()
    assert refreshed_src == first_src, "A capa mudou após simples atualização da página."


@pytest.mark.asyncio
@pytest.mark.visual
async def test_ct_capa_002_respeita_tamanho_proporcao_e_posicao(
    detail_page: ProductDetailPage,
    settings: Settings,
) -> None:
    await detail_page.open(settings.title_main_id)
    rect = await detail_page.relative_cover_rect()
    metadata = await detail_page.image_metadata()

    assert_close(
        rect.width,
        settings.expected_cover_width_px,
        settings.geometry_tolerance_px,
        "Largura da capa",
    )
    assert_close(
        rect.height,
        settings.expected_cover_height_px,
        settings.geometry_tolerance_px,
        "Altura da capa",
    )
    assert_close(
        rect.x,
        settings.expected_cover_x_relative_px,
        settings.geometry_tolerance_px,
        "Posição horizontal relativa",
    )
    assert_close(
        rect.y,
        settings.expected_cover_y_relative_px,
        settings.geometry_tolerance_px,
        "Posição vertical relativa",
    )

    rendered_ratio = rect.width / rect.height
    natural_ratio = metadata["naturalWidth"] / metadata["naturalHeight"]
    assert math.isclose(
        rendered_ratio,
        natural_ratio,
        abs_tol=settings.aspect_ratio_tolerance,
    ), (
        "A imagem está deformada: a proporção renderizada difere da proporção natural "
        f"além da tolerância {settings.aspect_ratio_tolerance}."
    )


@pytest.mark.asyncio
@pytest.mark.visual
async def test_ct_capa_003_mantem_posicao_fixa_em_paginas_diferentes(
    detail_page: ProductDetailPage,
    settings: Settings,
) -> None:
    product_ids = [settings.title_main_id, settings.title_other_id, settings.title_third_id]
    positions: list[Rect] = []

    for product_id in product_ids:
        await detail_page.open(product_id)
        positions.append(await detail_page.relative_cover_rect())

    baseline = positions[0]
    for index, current in enumerate(positions[1:], start=2):
        assert_close(
            current.x,
            baseline.x,
            settings.geometry_tolerance_px,
            f"Posição horizontal da página {index}",
        )
        assert_close(
            current.y,
            baseline.y,
            settings.geometry_tolerance_px,
            f"Posição vertical da página {index}",
        )
        assert_close(
            current.width,
            baseline.width,
            settings.geometry_tolerance_px,
            f"Largura da capa na página {index}",
        )
        assert_close(
            current.height,
            baseline.height,
            settings.geometry_tolerance_px,
            f"Altura da capa na página {index}",
        )


@pytest.mark.asyncio
@pytest.mark.visual
async def test_ct_capa_004_nao_salta_com_quantidades_diferentes_de_dados_bibliograficos(
    detail_page: ProductDetailPage,
    settings: Settings,
) -> None:
    await detail_page.open(settings.title_few_bib_id)
    few_count = await detail_page.bibliographic_line_count()
    few_rect = await detail_page.relative_cover_rect()

    assert few_count == settings.expected_few_bib_lines, (
        f"Pré-condição inválida: esperado {settings.expected_few_bib_lines} linhas "
        f"bibliográficas no produto resumido, obtido {few_count}."
    )

    samples = await detail_page.open_and_collect_layout_samples(
        settings.title_many_bib_id,
        settings.layout_monitor_ms,
    )
    many_count = await detail_page.bibliographic_line_count()
    many_rect = await detail_page.relative_cover_rect()

    assert many_count == settings.expected_many_bib_lines, (
        f"Pré-condição inválida: esperado {settings.expected_many_bib_lines} linhas "
        f"bibliográficas no produto completo, obtido {many_count}."
    )
    assert many_count > few_count, "Os dados de teste não possuem quantidades bibliográficas diferentes."

    assert_close(
        many_rect.x,
        few_rect.x,
        settings.geometry_tolerance_px,
        "Posição horizontal entre produtos com poucos e muitos dados",
    )
    assert_close(
        many_rect.y,
        few_rect.y,
        settings.geometry_tolerance_px,
        "Posição vertical entre produtos com poucos e muitos dados",
    )

    # O monitor é instalado antes da navegação e coleta posições desde a primeira
    # renderização da capa, incluindo alterações causadas pela chegada tardia dos dados.
    observed_delta = max_position_delta(samples)
    assert observed_delta <= settings.max_layout_shift_px, (
        "A capa apresentou salto visual acima do limite permitido: "
        f"máximo observado {observed_delta:.2f}px; "
        f"limite {settings.max_layout_shift_px:.2f}px."
    )


@pytest.mark.asyncio
@pytest.mark.network
async def test_ct_capa_005_entrega_imagem_dimensionada_e_cacheada(
    detail_page: ProductDetailPage,
    settings: Settings,
) -> None:
    response = await detail_page.capture_cover_response(settings.title_main_id)
    metadata = await detail_page.image_metadata()

    assert 200 <= response.status < 400, f"Resposta HTTP inesperada para a capa: {response.status}."

    extension = image_extension(response.url, response.headers.get("content-type"))
    assert extension in settings.allowed_image_formats, (
        f"Formato de imagem '{extension}' não pertence à lista permitida "
        f"{settings.allowed_image_formats}."
    )

    natural_width = float(metadata["naturalWidth"])
    natural_height = float(metadata["naturalHeight"])
    rendered_width = float(metadata["renderedWidth"])
    rendered_height = float(metadata["renderedHeight"])

    assert natural_width >= rendered_width * settings.min_image_scale_factor
    assert natural_height >= rendered_height * settings.min_image_scale_factor
    assert natural_width <= rendered_width * settings.max_image_scale_factor, (
        "A largura natural da imagem é excessivamente maior do que a largura exibida, "
        "indicando sobrecarga de dados."
    )
    assert natural_height <= rendered_height * settings.max_image_scale_factor, (
        "A altura natural da imagem é excessivamente maior do que a altura exibida, "
        "indicando sobrecarga de dados."
    )

    assert response.body_size > 0, "Não foi possível determinar o tamanho transferido da imagem."
    assert response.body_size <= settings.max_image_bytes, (
        f"Imagem com {response.body_size} bytes excede o limite configurado "
        f"de {settings.max_image_bytes} bytes."
    )

    policy = parse_cache_control(response.headers.get("cache-control"))
    assert not policy.no_store, "A imagem foi entregue com 'no-store', contrariando o cache prolongado."
    assert policy.max_age is not None, "O cabeçalho Cache-Control não define max-age ou s-maxage."
    assert policy.max_age >= settings.min_cache_max_age_seconds, (
        f"Cache de {policy.max_age}s é inferior ao mínimo aprovado de "
        f"{settings.min_cache_max_age_seconds}s."
    )

    if settings.require_immutable_cache:
        assert policy.immutable, "O cache prolongado não utiliza a diretiva 'immutable'."

    if settings.require_versioned_image_url:
        assert has_version_marker(response.url), (
            "A URL da imagem não apresenta hash ou parâmetro de versão. "
            "Sem versionamento, cache prolongado pode impedir a atualização da capa."
        )

    # Segunda navegação no mesmo contexto: além dos cabeçalhos, confirma a
    # reutilização efetiva por cache de memória/disco ou service worker.
    first_src = str(metadata["src"])
    cache_observation = await detail_page.observe_cover_cache_on_reload(first_src)
    second_src = str((await detail_page.image_metadata())["src"])
    assert second_src == first_src, "A URL versionada da capa mudou sem alteração de conteúdo."
    assert cache_observation.served_from_cache, (
        "A imagem não foi reutilizada pelo cache no segundo acesso. "
        f"Bytes codificados observados: {cache_observation.encoded_data_length}."
    )
