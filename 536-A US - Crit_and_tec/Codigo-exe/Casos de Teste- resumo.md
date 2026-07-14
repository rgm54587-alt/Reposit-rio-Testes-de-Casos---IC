# Revisão de aderência aos critérios de aceitação

## CT-BUSCA-001 — Autocomplete até o terceiro caractere

**Critérios cobertos**

- Exibição com os primeiros caracteres e, no máximo, a partir da terceira letra.
- Abertura sem atraso perceptível.
- Exibição de um resultado desejado e previamente definido.

**Problema encontrado e resolução**

O termo “sem atraso perceptível” não possui valor objetivo. O teste usa `AUTOCOMPLETE_MAX_MS`, configurável no `.env`. O valor padrão de 500 ms é apenas uma referência inicial e precisa ser aprovado pela equipe. O código aceita abertura após o primeiro, segundo ou terceiro caractere, evitando exigir que o componente espere exatamente três letras.

## CT-BUSCA-002 — Ocultação de ProductAvailability (40)

**Critério coberto**

- O título `ProductAvailability` e registros internos de tipo 40 não devem ser exibidos.

**Problema encontrado e resolução**

O critério não informa como o tipo 40 aparece no HTML. O teste sempre valida que o título não está visível e, quando a aplicação expõe um marcador técnico, usa `INTERNAL_TYPE_SELECTOR`. Isso valida o comportamento visível sem exigir uma tecnologia específica de backend.

## CT-BUSCA-003 — Espaços e letras esquecidas

**Critérios cobertos**

- Busca com espaços indevidos ou letras ausentes.
- Proposta de “Você quis dizer?”.

**Problema encontrado e resolução**

A localização da sugestão não está definida. O teste não exige posição, cor ou layout. Ele aceita duas implementações válidas: retorno direto do produto correto ou apresentação de uma sugestão que contenha o termo esperado e que possa ser selecionada.

## CT-BUSCA-004 — Busca curinga sem termo

**Critérios cobertos**

- Campo vazio executa uma pesquisa equivalente a `*`.
- Enter possui comportamento equivalente ao clique na lupa.

**Problema encontrado e resolução**

O critério não define a lista exata nem a ordem da busca `*`. O teste exige produtos pesquisáveis e compara Enter com lupa na mesma execução e ambiente. Caso o sistema use resultados personalizados ou aleatórios, a comparação exata de ordem deverá ser substituída por uma regra de equivalência aprovada.

## CT-BUSCA-005 — Enter, lupa e ausência de resultados

**Critérios cobertos**

- Enter funciona como a lupa.
- Uma mensagem é apresentada quando não há resultado.

**Problema encontrado e resolução**

Comparar apenas a URL poderia gerar falso positivo, e comparar apenas o conteúdo poderia ignorar rotas diferentes. O teste compara URL normalizada, lista e ordenação dos resultados. Para a busca inexistente, exige zero resultados válidos e uma mensagem cujo texto é configurável por `NO_RESULTS_TEXT`.

## Conclusão

A suíte cobre todos os critérios fornecidos, mas quatro definições ainda precisam de aprovação formal para eliminar subjetividade:

1. limite máximo do autocomplete;
2. texto oficial da mensagem sem resultados;
3. comportamento e ordenação da busca `*`;
4. texto e interação definitivos de “Você quis dizer?”.
