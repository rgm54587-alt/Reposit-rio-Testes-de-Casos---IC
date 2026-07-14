# Automação dos casos de teste de pesquisa

Suíte E2E em Python com `pytest` e Playwright para os casos CT-BUSCA-001 a CT-BUSCA-005.

## Estrutura

```text
product_search_tests/
├── pages/
│   └── search_page.py
├── tests/
│   ├── conftest.py
│   └── test_product_search.py
├── .env.example
├── CRITERIA_REVIEW.md
├── pytest.ini
├── requirements.txt
└── README.md
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

## Configuração

Copie `.env.example` para `.env` e substitua:

- `BASE_URL` pela URL real;
- os dados de produtos pelos registros existentes no catálogo de teste;
- os seletores pelos atributos estáveis da aplicação;
- `AUTOCOMPLETE_MAX_MS` pelo limite aprovado;
- os textos pelas mensagens oficiais do produto.

Evite seletores baseados apenas em posição ou classes CSS geradas. Prefira `data-testid`.

## Execução

```bash
pytest --browser chromium
```

Para executar apenas um caso:

```bash
pytest tests/test_product_search.py::test_ct_busca_001_autocomplete_abre_ate_o_terceiro_caractere --browser chromium
```

Para abrir o navegador durante a execução:

```bash
pytest --browser chromium --headed
```

## Observações importantes

- Os testes não inventam URLs, produtos ou mensagens reais; esses dados ficam no `.env`.
- O teste de desempenho mede o tempo entre o terceiro caractere e a visibilidade do autocomplete. Se o autocomplete abrir antes, o critério funcional é considerado atendido.
- O teste de “Você quis dizer?” aceita resultado corrigido diretamente ou sugestão clicável.
- O teste de `ProductAvailability (40)` valida a ausência de exposição ao cliente. Uma validação de backend exige uma API ou acesso ao índice de busca.
- A coleta pelo `pytest` valida estrutura e sintaxe, mas a execução completa depende da aplicação real.
