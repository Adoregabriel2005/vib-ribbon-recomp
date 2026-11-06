# Registro de validação — 05/11/2026

## Concluído

- New Project Layout oficial, submódulos fixados e disco externo.
- Identidade do disco e seeds em `disc_probe.json` e `catalog_identity.json`.
- Inventário de 24 arquivos em `reports/disc_inventory.json`.
- Emissores de jogo e BIOS compilados para Windows x64.
- Geração de 107 funções do boot em C; limites de funções ainda são heurísticos.
- Três imagens AOT extraídas e 28.335 variantes auditadas contra bytes do disco.
- Configuração completa do runtime com REFERENCE, LLE e OpenBIOS.
- Console offline verificado; fontes geradas conferidas por SHA-256.
- Aplicativo nativo compilado e vinculado: `build-runtime/VibRibbon_Recompiled.exe`.
- Boot headless alcançou a seleção original de idioma; captura em
  `reports/language-screen.png`. Referência externa não foi comparada.
- Log confirma OpenBIOS LLE, scheduler LLE e resolução nativa selecionados.
- Ferramentas oficiais de overlay preparadas com compilador GCC local;
  runtime confirma autocompile habilitado e cache ativo.
- Probe `reports/boot-with-cache.json`: frame 2697 no snapshot de diagnóstico,
  7.588.351 hits de despacho estático, 3.082.591 hits do shard AOT,
  3.099 despachos de cache nativo, 2.433 blocos/111.883 instruções interpretadas,
  zero aborts do interpretador e zero falhas de despacho observadas.
  São contadores de unidades diferentes e instantes próximos, não uma porcentagem.
- Esse snapshot retornou todos os oito PCs resumidos de fallback (8/8).
  Não comprova logging integral de cada instrução nem cobertura do jogo inteiro.
- SPU produziu amostras não nulas no probe; CDDA e saída de áudio host não foram
  exercitados nesse modo headless. Zero underruns ali não valida áudio real.
- Probe OpenGL oculto: renderer inicializado com resolução nativa e batching LLE;
  todas as consultas do painel retornaram JSON válido após substituir o exportador
  de timing problemático. O diagnóstico aceitou a injeção de Cross, mas o probe
  de 30 segundos continuou na seleção de idioma; a animação não prova mudança de
  menu. Evidência inicial em `reports/opengl-first.json` e
  `reports/opengl-transition.png`.

## Em validação

- Navegação de idioma confirmada: duas entradas Cross separadas após o frame
  1400 alcançaram GAME / HOW TO PLAY / LANGUAGE. Evidências preservadas em
  `reports/main-menu-confirmed.json` e `.png`. Polling SIO, buffer libpad e
  máscara de confirmação foram observados, sem alterar o código original.
- Entrada em GAME carregou MAIN_G.EXE (assinatura em 0x80019180), mas interrompeu
  na tela LOADING: `DISPATCH FATAL: misaligned target 0x0000FFFF`, RA 0xFFFF,
  COP0_EPC 0x80059588. Evidências em `reports/game-load-failure.json`, `.log`
  e `.png`. A causa ainda não foi determinada; não atribuir à BIOS sem comparação.
- O processo mantém o servidor ativo após falha e pode encerrar com código zero.
  O probe agora também verifica marcadores fatais no log e retorna falha nesse caso.
- Build separado `build-diagnostics`, habilitado por `scripts/build.ps1 -Diagnostics`,
  permite rastros de funções e PCs sem substituir o aplicativo visível do usuário.
- Correção local no runtime: a troca de PCB[0] dentro do IRQ era respeitada pelo
  scheduler HLE, mas não pela ponte LLE de fibras. O RFE restaurava o contexto da
  nova thread (PC 0x80025428), enquanto o bloco nativo interrompido continuava na
  pilha anterior. Agora a ponte suspende a pilha anterior e executa a thread alvo
  usando o TCB já salvo pelo próprio kernel; não salva os registradores da thread
  alvo sobre o contexto anterior. Ao retornar, restaura o estado da continuação.
- Mesmo probe que falhava passou do carregamento e exibiu a seleção original
  “Play with the vib-ribbon disc”; mais de 4.000 frames, sem marcadores fatais.
  Evidências em `reports/irq-fiber-fix.json`, `.log` e `.png`. OpenBIOS e LLE
  mantidos. Isso valida essa transição, não a fidelidade do jogo completo.
- Versão normal recompilada com a correção em `build-runtime`.
- Repetição na versão normal alcançou frame 5672, obstáculos em movimento e
  2.270.592 frames CDDA não nulos, sem marcadores fatais. Evidências preservadas
  em `reports/release-gameplay.json`, `.log` e `.png`. Probe headless de 40 s;
  não é teste de estabilidade prolongada nem saída host de áudio.
- Probe seguinte confirmou Round 1, Vibri e obstáculos após selecionar o disco:
  `reports/gameplay-first.json`, `.log`, `.png` e `reports/round-one.png`.
  Frame final observado 4660; sem marcadores fatais. CDDA `cd_in` produziu
  1.591.128 frames, dos quais 1.563.843 não nulos, e SPU 3.070.216 frames
  não nulos. O tap host é zero por ser headless; não comprova áudio ouvido no PC.
  Há traços coloridos/fragmentados nas capturas que ainda requerem comparação
  visual. Não declarar fidelidade de renderização, ritmo ou colisões.
- Transições de programas, demais menus e gameplay.
- Registro integral de fallback, expansão da cobertura e áudio host/CDDA.


## MP3 e menus nativos - 05/11/2026

- Build `build-native-ui`: menu de musicas e opcoes PC, integrado aos estados
  verificados do CD proprio e OPTIONS, alem de F10/Ctrl+L. Hooks restritos aos
  bytes e GP do overlay MAIN_G. Preservados OpenBIOS, REFERENCE e LLE.
- minimp3 CC0 decodifica MP3; SDL3 converte para CDDA 44.1 kHz/16-bit/estereo.
  CUE/BIN em cache, sem mudar os originais. O proprio jogo analisa o audio e
  gera obstaculos. Nao ha player externo sobreposto.
- Testadas Amigas (161,254 s) e Tudo Tudo (94,157 s), fornecidas pelo usuario.
  `reports/amigas-first` chegou ao gameplay manual; `reports/tudo-auto-first`
  chegou ao Auto original sem entradas de gameplay apos escolher o modo.
  CDDA e host produziram audio nao nulo. Fim de faixa, pausa/retomada e
  sincronizacao contra referencia ainda requerem validacao.
- GetID e ReadN/ReadS corrigidos para disco somente de audio; isso removeu a
  espera indefinida ao testar a musica como disco de dados. Testes de CD FIFO,
  IRQ/DMA, identificacao e troca de disco passaram. Musica nao muda o boot salvo.
- Backend Windows de drive fisico/virtual: TOC e leitura RAW CDDA implementados.
  Nao houve teste com dispositivo e CD real. Nao declarar hardware validado.
- Opcoes PC de janela, tela cheia, renderizador, resolucao interna, VSync e
  volume. Persistencia volume/janela e rejeicao de volume invalido testadas.
  Ainda verificar cada opcao ao vivo e navegacao completa por controle.
- PT-BR inicial da interface PC. Textos do disco e selecao de idiomas pendentes.
  Botao Demo oficial ainda requer teste.
- Novo Demo MP3: sincroniza o modo do menu (GP+0x580) e do controlador de
  sessao (GP+0x840). Alterar somente o primeiro iniciava partida manual e
  resultava em Game Over. O codigo original em 0x80050278 consulta o segundo;
  o novo probe exibiu *Auto* no gameplay com Tudo Tudo. Evidencia final em
  `reports/integrated-tudo-demo-corrected` (150 s, sem marcadores fatais).
- Patches adicionais: `patches/audio-cd-media.patch` e
  `patches/pc-volume-settings.patch`, ja aplicados aos submodulos locais.

## Ainda não comprovado

| Componente | Evidência necessária |
| --- | --- |
| CPU/memória/BIOS | Boot, troca de programas, exceções e código modificado |
| GPU/GTE | Capturas pareadas de menus, obstáculos e animações |
| DMA/CD-ROM | Sequência de leituras e transições sem falhas |
| CDDA/SPU | Todas as faixas oficiais, efeitos, pausas e transições |
| Timers/IRQ/scheduler | Ritmo e sincronização audiovisual medidos |
| Controles | Todas as ações, combinações e latência |
| Memory cards | Salvar, reiniciar e carregar sem perda |
| Gameplay | Obstáculos, colisões, pontuação e progressão contra referência |
| Cobertura | Separar estático, variantes dinâmicas e instruções interpretadas |
| Instrumentação | Paginação/truncamento e registro integral de fallback |

## Falhas de ferramentas observadas

1. O scaffold escolheu o bash do WSL indisponível ao escrever os pins;
   `framework_pins.txt` foi refeito com hashes Git reais.
2. `python` é um alias indisponível; há Python 3.14.6 instalado.
3. O CLI exige Ninja mesmo com Makefiles existentes; o script usa emissores
   oficiais diretamente, sem alterar o runtime.
4. Fragmentos isolados opcionais falharam na auditoria em `0x800406C8`.
   Reprodução em `.cache/aot-static/disc-aot-sh6gp1vp/`. O conjunto publicado
   passou pela auditoria com essa expansão desabilitada.
5. OpenBIOS: quatro funções ignoradas e alvos não emitidos. Não remover
   fallback nem declarar compatibilidade antes do teste.
6. Sockets localhost foram bloqueados no teste restrito; repetir fora desse
   ambiente permitiu coletar os contadores e a captura. O processo do probe foi encerrado.
7. O leitor inicial tratava uma linha como uma resposta completa. Rastros podem
   distribuir um objeto JSON por várias linhas. O leitor acumula até obter JSON
   completo, com limite de tamanho e testes de regressão. A atribuição anterior
   de JSON inválido ao runtime não foi comprovada. O painel usa `latency`, `perf`
   e `cdrom_state`; o exportador de timing específico ainda requer novo teste.

Não há execução de referência registrada nem resultado de fidelidade aprovado.

### Medidas do Demo MP3 integrado

`integrated-tudo-demo-corrected.json`: frame 9319; CDDA 4.156.572 frames
(4.135.250 nao nulos), host 6.469.029 (5.862.849 nao nulos), captura final
com *Auto*, sem erro fatal. Sete entradas de navegacao, ultima no frame 4909;
nenhum comando de obstaculo. Probe usa turbo somente no inicio ate frame 3900.
Ha underruns e drops na ponte de audio; os totais incluem o trecho acelerado.
Nao declarar audio sem falhas ou sincronizacao aprovada. Retorno ao menu apos
o fim da faixa ainda nao foi observado nesse probe.

## Organizacao para testes publicos - 06/11/2026

- Abertura MP3 por arquivo mapeado (API wide no Windows), eliminando a copia
  completa do MP3 na memoria. As duas musicas de teste produziram PCM idêntico
  byte a byte ao conversor anterior e passaram pelo leitor CDDA.
- Build NativeUI recompilado e boot OpenGL de 20 s sem marcadores fatais.
- Configuracao local do disco separada em game.local.toml; template publico
  sem caminho do computador. Setup idempotente aplica os quatro patches.
- Patches testados sobre arquivos limpos dos pins, com reversao bem-sucedida.
- Publicacao apenas de fontes manuais e perfis: generated/, reports/, caches,
  saves, discos e musicas ficam locais. Historico detalhado acima referencia
  evidencias locais que nao acompanham o repositorio publico.
- CI sem ROM: ferramentas, traducao e verificacao do conteudo Git. Nao e
  um teste de fidelidade nem uma release binaria para jogadores finais.
- Dez testes Python passaram, incluindo aplicacao/reversao dos patches em
  fontes limpas. Regressao nativa de identificacao CD e FIFO/IRQ/DMA passou.
