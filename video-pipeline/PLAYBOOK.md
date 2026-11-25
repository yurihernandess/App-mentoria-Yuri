# Playbook – Vídeos de acompanhamento de obra Rogga (Hernandes Negócios Imobiliários)

Rotina semanal executada por uma tarefa agendada. Objetivo: assim que a Rogga publicar
as fotos de drone de um novo mês, gerar os vídeos e um calendário de postagem que cubra as semanas seguintes.

## Quando a Rogga publica (levantado em 25/11/2026)
- Joinville: todas as obras no mesmo lote, entre os dias 10 e 20 do mês seguinte
  (set/26 publicado em 20/10; out/26 em 11/11; ago/26 em 10/09).
- Litoral (Penha, Balneário Piçarras, Barra Velha): lote separado, cerca de 1 semana depois
  (out/26 publicado em 16/11).
- Responsável na Rogga: Letícia Fernandes (pasta "Drones Obras").

## Fontes (Drive Rogga, compartilhado por link)
- Drones Obras: `1OZNZ9tSaI42g2g3zJ8ukidaWoLOVZuDg`
  - Joinville `1fSIHUE1akzse1LhFal1tz1pmV3P-6tYU` · Penha `1KLIlI1Whh8p5Xh6N1byoat2qZMrc5NaP`
  - Balneário Piçarras `1SnI85jAlND5yWGA3UzU9fBVpLbGaPS6u` · Barra Velha `1Wapmr2H5ajN06WWlMs-OfAmqhYlOvyss`
- Produtos (renders 3D, logos, plantas): `1S3qZploO2HCxv0HE4wFnRYQsDoBgw0jn` (Joinville `1m7FNMqRswqAboULSrIkG6_usESzlGZHl`).
  `tools/prod_files.json` já tem o mapeamento dos renders de Joinville.
- Listar pasta pública: `node tools/list2.js <folderId> <profundidade>`.
- Baixar arquivo: `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t`.
- Data de publicação de uma pasta: Google Drive MCP `get_file_metadata` (campo createdTime).

## Estado
`state.json` guarda o último mês processado por obra. Depois de cada rodada, atualize, faça commit e push
na branch `claude/real-estate-video-editing-pzs9xv`. Nunca versione fotos ou vídeos (ver `.gitignore`).

## Passo a passo semanal
1. Liste as pastas de mês de cada obra. Se nenhuma obra tiver um mês mais novo que o `state.json`, encerre a rodada
   sem produzir nada, apenas com uma notificação curta ("sem fotos novas").
2. Para as obras com mês novo:
   - Baixe o histórico de meses em `joinville/months/` com `tools/fetch_all.py` e escolha as fotos com `tools/pick.py`
     (mesmo ângulo mês a mês). Faça uma folha de contato e confira visualmente.
   - **Reels 9:16 por empreendimento** (`evo.py`, um spec por obra). Rodar os 7 estilos
     `morph, slider, hyper, mosaic, polaroid, triptych, rewind`, trocando o estilo de cada obra todo mês
     (estilo = lista[(índice_da_obra + número_do_mês) % 7]), para não repetir o padrão.
   - **Reel do litoral** com Penha + Piçarras + Barra Velha juntas (`engine.py`, modelo `specs/O_litoral3.py`).
   - **Resumão YouTube 16:9 Joinville** (`yt_obras.py`, modelo `specs/YT_obras_jv.py`): projeto (renders), obra (timelapse), hoje.
3. Faça a conferência (QC) extraindo quadros de cada vídeo e olhando: textos sem corte, datas certas, nome certo.
4. Monte `CALENDARIO_<mes>.md`: 1 Reel por dia útil, intercalando Joinville e litoral, até cobrir as semanas
   até o próximo lote. YouTube na primeira segunda-feira.
5. Entregue os MP4 com SendUserFile e envie uma notificação push resumindo o que ficou pronto e o calendário.

## Regras de conteúdo
- Usar só informação confirmada. Em renders, sempre "Imagem ilustrativa". Na legenda, citar "Imagens: Rogga".
- Urban Orquídeas já foi ENTREGUE (confirmado pelo Yuri em 25/11/2026).
- Identidade: azul #091A36 e dourado #B39058, WhatsApp (47) 92001-5396, @imobiliariahernandes, CRECI 11540J.
- Sem trilha musical (o Yuri coloca no Edits); só efeitos sonoros.
- Não pedir confirmação para detalhes de edição. Decida e entregue.

## Dependências
ffmpeg, Python 3 com Pillow e numpy, Node com Playwright (já vêm no ambiente). Fontes Inter e JetBrains Mono do sistema.
