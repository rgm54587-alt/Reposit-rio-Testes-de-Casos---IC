# Automação dos casos de teste de registro e login no checkout

Projeto de testes E2E em Python usando `pytest` e Playwright.

## O que é validado

- CT-REG-001: opções de login/cadastro, login de cliente existente, botão “Let's go”, dados e carrinho preservados.
- CT-REG-002: endereço anterior preservado, senha e repetição, rótulo correto de e-mail e resumo do endereço.
- CT-REG-003: e-mail inválido interceptado e erro genérico contra enumeração de usuário.
- CT-REG-004: persistência no banco, senha não armazenada em texto aberto, e-mail padrão e bloqueio antes da confirmação.
- CT-REG-005: confirmação em 167h59 aceita e confirmação em 168h01 rejeitada.

## Preparação

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Ajuste o `.env` para o ambiente de testes. Nunca use banco de produção.

## Contrato de seletores

A aplicação deve disponibilizar os `data-testid` utilizados em
`pages/checkout_page.py`, por exemplo:

- `add-to-cart`, `open-cart`, `cart-item`, `checkout-cart-item`, `checkout`
- `login-option`, `register-option`, `lets-go`, `checkout-address`
- `login-form`, `login-email`, `login-password`, `login-submit`
- `register-from-address`, `registration-form`, `register-email`
- `register-password`, `register-password-repeat`, `register-submit`
- campos do endereço e mensagens descritos no Page Object

Caso a aplicação não use `data-testid`, altere somente o Page Object.

## Banco de dados

As consultas SQL são configuráveis pelo `.env`, pois o schema real não foi
fornecido. O teste espera que a consulta de cliente retorne as chaves:

- `email`
- `status` (valores válidos configurados por `PENDING_STATUSES` e `ACTIVE_STATUSES`)
- `password_hash`
- `created_at`
- `confirmed_at`
- `confirmation_expires_at`

Para o teste de sete dias, a consulta de atualização deve receber, nesta ordem:
`created_at`, `confirmation_expires_at` e `email`.

## Caixa de e-mail

O cliente foi preparado para uma API compatível com MailHog. Se o projeto usar outro serviço,
substitua apenas `services/mailbox.py`, mantendo os métodos:

- `wait_for_message(recipient)`
- `body_text(message)`
- `confirmation_url(message)`

## Execução

```bash
pytest -v
```

Somente os testes de segurança:

```bash
pytest -v -m security
```

Somente integração e retenção:

```bash
pytest -v -m "integration or retention"
```

## Decisões tomadas na revisão dos critérios

1. O validador de sintaxe pode indicar que o formato do e-mail é inválido antes
do envio. Depois do envio, falhas de negócio usam somente a mensagem genérica
`Registration not correct`.
2. O cadastro é persistido imediatamente como pendente. Login completo e
continuidade com os dados cadastrados só são liberados após a confirmação.
3. “Retido por sete dias” foi convertido em 168 horas. O limite é testado em
167h59 e 168h01 para evitar um teste instável exatamente no instante de corte.
4. “WK” foi interpretado como a área de login do carrinho/checkout. A rota é
configurável por `CHECKOUT_LOGIN_URL_PATTERN`.
5. Os textos-padrão não foram fornecidos; por isso são valores configuráveis e
devem ser substituídos pelas frases oficialmente aprovadas pelo produto.
