# Menus e modos do Vib-Ribbon Recomp

Requisitos definidos pelo usuário em 04/11/2026, a partir das telas GAME e
OPTIONS do jogo. Este documento especifica o produto; os recursos abaixo ainda
não estão implementados nem validados, salvo indicação explícita em STATUS.md.

## Entrada pelo menu original

Preservar o estilo de linhas brancas, fundo preto e animações de Vibri.
Integrar a interface nativa nos pontos reais dos menus, mantendo navegação por
teclado e controle, foco visível e retorno consistente ao jogo.

- **Jogar com o disco do Vib-Ribbon:** músicas oficiais pelo caminho original
  CD-ROM/CDDA/SPU, usando o disco do jogo configurado.
- **Minhas músicas:** substituir a entrada “Play with my own choice of CD” por
  um menu de seleção de fonte com **Arquivos MP3** e **CD de áudio**. A função
  original de CD continua disponível dentro desse menu.
- **Opções:** ampliar a entrada OPTIONS com as configurações nativas do port,
  preservando as opções originais de efeitos sonoros e vibração.

## Minhas músicas

**Arquivos MP3:** selecionar arquivos/pastas locais, mostrar título e duração,
selecionar faixa e dificuldade e iniciar Jogar ou Demo. Uma biblioteca musical
poderá organizar os arquivos sem exigir alterar ou copiar os originais.
Decodificação e análise devem alimentar o mecanismo de geração de obstáculos
do jogo; tocar um MP3 por cima de uma fase fixa não satisfaz este requisito.

**CD de áudio:** escolher um drive físico ou virtual disponível no Windows,
ler a lista de faixas de áudio e selecionar a faixa. Deve acessar o dispositivo
real/montado, não apenas mudar o nome de uma seleção de arquivo. Tratar mídia
ausente, disco sem áudio, troca/ejeção e indisponibilidade do drive, permitindo
voltar ao menu. Suporte a imagens de disco pode complementar essa entrada, mas
não substitui o suporte solicitado a drives físicos e virtuais.

A integração com dispositivos Windows e o formato entregue ao runtime precisam
ser investigados. Não anunciar suporte a hardware antes de testar leitura,
reprodução, posição da faixa e troca de mídia. Não acessar exclusivamente ou
ejetar dispositivos durante detecção automática.

## Modos de execução

- **Jogar:** o usuário controla Vibri, com obstáculos, combinações, colisões,
  pontuação e progressão do jogo. Disponível para músicas oficiais e próprias.
- **Demo / Assistir:** a máquina joga automaticamente para o usuário apreciar
  a música escolhida e as animações. Disponível para músicas oficiais, MP3 e CD.
  Exibir claramente o modo; resultados automáticos não contam como recordes,
  desbloqueios ou progresso de uma partida manual.

O modo Demo deve usar os eventos e as regras de entrada do jogo. Um controle
automático será integrado após mapear os obstáculos e as janelas de acerto;
não usar simples invencibilidade como substituto de um jogador automático.
Pausa, saída e reinício precisam funcionar nos dois modos. Ao sair de Demo,
devolver imediatamente o controle manual sem deixar botões presos.

## Opções do recomp

| Categoria | Configurações previstas |
| --- | --- |
| Tela | Resolução da janela, monitor, janela/tela cheia/sem bordas, proporção e escala |
| Gráficos | Resolução interna, sincronização vertical, filtros/antialiasing e melhorias que o backend realmente oferecer, com preset Original |
| Som | Volume geral, música e efeitos, dispositivo de saída e ajuste de latência/sincronia quando suportado |
| Controles | Teclado e gamepad, remapeamento, vibração e restauração dos padrões |
| Idioma | Idioma da interface e dos textos do jogo; incluir Português do Brasil |
| Dados | Seleção de músicas e drive, saves/memory cards e preferências persistentes |

Oferecer somente controles ligados a recursos reais. Manter velocidade e
temporização originais independentes da resolução/FPS do monitor. Oferecer
Aplicar/Cancelar e recuperação de uma configuração de vídeo que deixe a tela
inacessível. Respeitar alterações existentes do usuário.

## Idiomas

Incluir PT-BR e preservar as cinco línguas do disco europeu: inglês, francês,
alemão, espanhol e italiano. Separar strings da interface nativa do código;
armazenar identificadores estáveis e usar fallback para strings ausentes.
Mapear textos e recursos originais antes de implementar tradução dentro do jogo.
Suportar acentos e caracteres das línguas disponíveis, expansão de textos,
descrições dos comandos e menus de erro. Não considerar o jogo traduzido só
porque o launcher ou um menu de PC recebeu tradução.

## Ordem de implementação e validação

1. Consolidar áudio host, renderização, entradas, transições e estabilidade do
   jogo original, conforme ARCHITECTURE.md.
2. Mapear os pontos de menu e as opções existentes no framework; implementar
   configurações reais, persistência e localização da interface nativa.
3. Integrar seleção/decodificação/análise de MP3 ao gameplay original.
4. Integrar e testar CD de áudio em drives físicos e virtuais disponíveis.
5. Integrar Demo às mesmas regras de gameplay e ampliar a tradução do jogo.

Para cada fonte musical, verificar início/fim, pausa, retomada, sincronização,
troca de faixa e retorno ao menu. Validar Demo e Jogar separadamente. Comparar
as músicas oficiais com uma referência legítima, sem substituir seu áudio por
um player externo. Recursos modernos não mudam a arquitetura PSXRecomp.
