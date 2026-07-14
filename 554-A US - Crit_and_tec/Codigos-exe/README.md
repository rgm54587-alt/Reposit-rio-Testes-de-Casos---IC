# Automação da área de login da loja

Suíte em Python com Pytest e Playwright baseada nos casos CT-LOGIN-001 a CT-LOGIN-005.

## Estrutura

```text
store_login_tests/
├── pages/login_page.py
├── tests/conftest.py
├── tests/test_store_login.py
├── utils/config.py
├── utils/mailbox.py
├── .env.example
├── CRITERIA_REVIEW.md
├── pytest.ini
└── requirements.txt
```

## Instalação

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## Configuração

Copie `.env.example` para `.env` e adapte:

```bash
cp .env.example .env
```

Itens obrigatórios para execução real:

1. `BASE_URL` e `LOGIN_PATH`;
2. seletores `SEL_*` de acordo com o HTML da aplicação;
3. credenciais das contas de teste;
4. mensagens reais da aplicação;
5. cores aprovadas do wireframe;
6. MailHog ou IMAP para o CT-LOGIN-005.

Os seletores padrão utilizam `data-testid`, pois são mais estáveis do que classes CSS de apresentação.

## Execução

Todos os testes:

```bash
pytest -v
```

Somente um caso:

```bash
pytest -v tests/test_store_login.py::test_ct_login_004_rejeita_credencial_invalida_e_aceita_credencial_valida
```

Somente testes funcionais, sem os visuais:

```bash
pytest -v -m "not visual"
```

## Observações

- CT-LOGIN-001 falhará com uma mensagem de configuração enquanto as cores do wireframe estiverem com `__SET_FROM_WIREFRAME__`.
- CT-LOGIN-003 exige dois inputs no componente `Specialised databases`; ajuste `SEL_REFERENCE_INPUTS` caso a estrutura real seja diferente.
- CT-LOGIN-005 altera a senha da conta de recuperação. Use uma conta exclusiva e restaure o estado por fixture, API ou rotina do ambiente.
- O projeto não inclui credenciais reais.
