# Revisão dos critérios de aceitação e da automação

## Resultado geral

A suíte mantém os cinco casos de teste originais e cobre os critérios funcionais e visuais informados. Os pontos que dependem do sistema real foram externalizados no arquivo `.env`.

## Problemas encontrados e resolvidos

### 1. Cores não informadas

O critério define azul e branco, mas não fornece códigos RGB/HEX nem tokens do design system. Inserir um azul arbitrário produziria uma validação incorreta.

**Solução:** os cinco valores de cor são obrigatoriamente configurados no `.env`. O CT-LOGIN-001 apresenta uma falha de configuração clara enquanto os valores do wireframe não forem definidos, pois ignorar o teste ocultaria um critério obrigatório. Valores HEX e `rgb/rgba` são normalizados antes da comparação.

### 2. “Alinhado à direita” era subjetivo

Uma comparação apenas visual não teria critério objetivo.

**Solução:** o teste compara a coordenada da borda direita do botão com a borda direita do contêiner do acordeão, aceitando a tolerância configurada em `VISUAL_TOLERANCE_PX`.

### 3. “Mesmo comprimento e largura” não definia tolerância

Renderização, escala e arredondamento subpixel podem gerar diferenças pequenas.

**Solução:** largura e altura dos dois campos e do botão são comparadas com uma tolerância configurável.

### 4. Placeholder “desaparece ao digitar”

O atributo HTML `placeholder` continua existindo quando o usuário digita. Verificar apenas o atributo reprovaria uma implementação correta ou aprovaria uma incorreta.

**Solução:** a automação usa a pseudo-classe CSS `:placeholder-shown`, que representa o estado visual efetivo do placeholder.

### 5. Fonte do placeholder

O critério pede a mesma fonte do título, porém fina. A fonte de `::placeholder` não é necessariamente igual ao estilo principal do input.

**Solução:** o teste consulta `getComputedStyle(element, '::placeholder')`, compara a família tipográfica com `Online Shop` e exige peso inferior a 600.

### 6. Espaçamento igual ao de “Specialised databases”

O requisito não fornece um valor em pixels.

**Solução:** o teste mede o espaço vertical real entre dois campos do componente de referência e compara com o formulário de login. Caso o componente não esteja presente, o teste falha com uma mensagem que orienta a correção de `SEL_REFERENCE_INPUTS`, pois essa referência é necessária para validar o critério.

### 7. Login inválido e válido no mesmo caso

O caso de teste fornecido contém as duas tentativas dentro do CT-LOGIN-004. A automação preserva essa estrutura para manter rastreabilidade 1:1 com os cinco IDs.

**Observação:** em uma suíte maior, as tentativas podem ser separadas em dois IDs para relatórios ainda mais específicos.

### 8. Recuperação de senha depende de e-mail real

Sem acesso a uma caixa de e-mail, seria impossível validar o critério completo.

**Solução:** foi criado suporte a MailHog e IMAP. O teste aguarda a mensagem, extrai o link, redefine a senha e valida que o token não pode ser reutilizado.

### 9. Texto e seletores variam entre aplicações

Mensagens, rotas e atributos HTML não foram fornecidos.

**Solução:** textos e seletores são configuráveis no `.env`. A automação assume `data-testid` apenas como padrão recomendado.

## Matriz de aderência

| Critério de aceitação | Teste |
|---|---|
| Renomear “Login area” para “Login centre” | CT-LOGIN-001 |
| Acordeão alinhado à direita | CT-LOGIN-001 |
| Estados azul/branco | CT-LOGIN-001 |
| Abrir menu suspenso | CT-LOGIN-002 |
| “Shop Login” para “Online Shop” em negrito | CT-LOGIN-002 |
| Espaçamento igual a “Specialised databases” | CT-LOGIN-003 |
| Design conforme wireframe | CT-LOGIN-001 e CT-LOGIN-003 |
| Mesmas dimensões | CT-LOGIN-003 |
| Placeholder dentro do campo e desaparece | CT-LOGIN-003 |
| Mesma fonte, sem negrito | CT-LOGIN-003 |
| “e-mail address” e “password” | CT-LOGIN-003 |
| Botão “Login” | CT-LOGIN-003 e CT-LOGIN-004 |
| Login funcional | CT-LOGIN-004 |
| “Forgot password” funcional | CT-LOGIN-005 |

## Limitações honestas

A suíte não pode comprovar fidelidade total ao wireframe sem que os códigos de cor, os seletores reais e o componente de referência sejam configurados. Também depende de contas de teste válidas e de uma caixa de e-mail controlada.
