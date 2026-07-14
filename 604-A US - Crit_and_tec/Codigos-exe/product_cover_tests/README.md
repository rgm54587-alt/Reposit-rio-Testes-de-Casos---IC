# Testes automatizados da capa na página de detalhes

Suíte em Python com `pytest` e Playwright para os casos `CT-CAPA-001` a `CT-CAPA-005`.

## Estrutura

```text
product_cover_tests/
├── pages/detail_page.py
├── tests/conftest.py
├── tests/test_product_cover.py
├── utils/config.py
├── utils/http_cache.py
├── .env.example
├── CRITERIA_REVIEW.md
├── pytest.ini
└── requirements.txt
```

## Instalação

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependências e o navegador:

```bash
pip install -r requirements.txt
playwright install chromium
```

Copie o arquivo de configuração:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Configuração obrigatória

Ajuste no `.env`:

- URL e rota da página de detalhes;
- IDs dos produtos de teste;
- seletores reais do DOM;
- dimensões e posição da capa obtidas da captura de tela;
- tolerâncias aprovadas;
- política oficial de cache;
- limites de dimensões e bytes.

Prefira atributos estáveis como `data-testid`. Não use classes CSS geradas automaticamente.

## Execução

```bash
pytest -v
```

Executar somente validações visuais:

```bash
pytest -v -m visual
```

Executar somente cache e rede:

```bash
pytest -v -m network
```

## Observações importantes

1. `EXPECTED_COVER_*` contém valores de exemplo. Substitua-os pelos valores do wireframe.
2. `MIN_CACHE_MAX_AGE_SECONDS=31536000` representa um ano e não deve ser tratado como regra definitiva sem aprovação técnica.
3. A URL da imagem precisa conter versão ou hash quando o cache for prolongado.
4. O teste de salto visual mede a posição da capa desde a primeira renderização. Para um orçamento formal de Core Web Vitals, complemente a suíte com medição de CLS.
5. O teste de cache usa telemetria do Chromium para confirmar reutilização em memória, disco ou service worker.
6. As imagens de teste precisam existir e ter dados bibliográficos controlados.
