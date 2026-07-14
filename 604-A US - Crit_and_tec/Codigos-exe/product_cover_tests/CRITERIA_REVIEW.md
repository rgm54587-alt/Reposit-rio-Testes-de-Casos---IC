# Revisão dos critérios de aceitação

## CT-CAPA-001 — Capa correspondente

O teste valida a associação entre produto e imagem usando título, autor, URL da capa e texto alternativo. A URL é comparada por um token configurável, pois sistemas reais podem usar CDN, transformações e hashes.

**Problema evitado:** comparar o nome completo e fixo do arquivo causaria falsa falha quando a CDN acrescentasse hash ou parâmetros.

## CT-CAPA-002 — Tamanho, proporção e posição

As medidas são relativas ao contêiner de detalhes, não ao viewport inteiro. Isso reduz falsas falhas provocadas por cabeçalhos, banners ou margens externas ao componente.

**Dependência pendente:** os valores do `.env` devem vir da captura de tela ou do wireframe oficial. Os valores fornecidos são apenas exemplos de configuração.

## CT-CAPA-003 — Posição fixa entre páginas

O teste compara três produtos e exige a mesma área estrutural para a capa. A comparação inclui posição e dimensões renderizadas.

**Problema evitado:** verificar apenas coordenadas absolutas poderia reprovar páginas equivalentes posicionadas em contêineres com margens externas diferentes.

## CT-CAPA-004 — Ausência de salto visual

O teste primeiro valida as pré-condições: um produto precisa ter poucas linhas bibliográficas e outro, muitas. Depois compara a posição relativa e coleta amostras para detectar deslocamento durante a estabilização da página.

**Limitação conhecida:** uma ferramenta dedicada de métricas web pode medir CLS com mais precisão. O teste atual mede o deslocamento real da capa, que é o comportamento exigido pelo critério.

## CT-CAPA-005 — Cache e dimensionamento

O critério “armazenadas em cache permanentemente” é tecnicamente ambíguo. A suíte o transforma em:

- `Cache-Control` com prazo mínimo configurável;
- diretiva `immutable`, quando exigida;
- URL versionada por hash ou parâmetro;
- dimensões naturais limitadas a um múltiplo das dimensões exibidas;
- tamanho máximo do arquivo configurável;
- reutilização efetiva no segundo acesso por cache de memória, disco ou service worker.

**Problema evitado:** exigir literalmente cache infinito impediria atualizações futuras da capa. Cache longo com versionamento atende à intenção sem congelar conteúdo antigo.

## Aderência geral

Os cinco critérios de aceitação são cobertos por cinco testes independentes. A suíte não assume tecnologia específica de layout, CDN ou backend. Seletores, medidas, tolerâncias, produtos e regras de cache são externos ao código e devem ser ajustados ao ambiente real.
