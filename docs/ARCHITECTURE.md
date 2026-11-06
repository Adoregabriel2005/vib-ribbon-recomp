# ADENDO TÉCNICO — ARQUITETURA DEFINITIVA DO VIB-RIBBON RECOMP

## DECISÃO ARQUITETURAL

A arquitetura foi definida:

RECOMPILAÇÃO NATIVA UTILIZANDO PSXRECOMP, COM RUNTIME DE HARDWARE COMPATÍVEL E SEM EMULADOR CONVENCIONAL.

Esta decisão é definitiva.

O projeto deve utilizar o PSXRecomp como infraestrutura de recompilação e execução.

Não substituir essa arquitetura por PCSX, DuckStation, RetroArch ou outro emulador convencional.

## 1. MODELO DE EXECUÇÃO

O funcionamento esperado é:

1. Identificar e extrair o executável do Vib-Ribbon.
2. Recompilar o código MIPS R3000A para código C utilizando PSXRecomp.
3. Compilar o código gerado para Windows x64.
4. Vincular o código ao runtime de hardware do PSXRecomp.
5. Utilizar o runtime para fornecer os serviços necessários do hardware original.
6. Executar o jogo como aplicação nativa de Windows.

O runtime não deve ser confundido com um emulador convencional.

A simulação de componentes de hardware é permitida e necessária para preservar o comportamento do jogo.

## 2. RECOMPILAÇÃO EM TRÊS NÍVEIS

Organizar a cobertura do código em três categorias:

NÍVEL 1 — RECOMPILAÇÃO ESTÁTICA

Todo código identificável previamente no executável principal deve ser recompilado para C e compilado nativamente.

NÍVEL 2 — OVERLAYS NATIVOS

Identificar códigos carregados dinamicamente pelo jogo a partir do disco.

Utilizar os recursos de captura, recompilação, cache e despacho nativo do PSXRecomp.

Investigar antecipadamente a possibilidade de recompilação dos overlays específicos do Vib-Ribbon.

NÍVEL 3 — INTERPRETADOR DE CONTINGÊNCIA

O interpretador do PSXRecomp pode ser utilizado quando houver código dinâmico ainda não recompilado.

Entretanto:

- Registrar toda execução pelo interpretador.
- Identificar os endereços e blocos envolvidos.
- Capturar os códigos dinâmicos.
- Tentar gerar versões nativas em cache.
- Registrar a cobertura de recompilação.
- Identificar os casos que não podem ser recompilados antecipadamente.

O interpretador não deve ser desativado prematuramente, pois isso pode causar falhas no jogo.

Objetivo: maximizar a execução nativa e minimizar progressivamente a utilização do interpretador.

Não declarar 100% de recompilação sem instrumentação e evidências.

## 3. RUNTIME DE HARDWARE

Utilizar preferencialmente os componentes já implementados no PSXRecomp.

Não criar substitutos redundantes.

Auditar especialmente:

- CPU e gerenciamento de memória.
- GPU e renderização.
- GTE.
- DMA.
- CD-ROM.
- CDDA.
- SPU.
- Timers.
- Interrupções.
- Controladores.
- Memory Cards.
- Sincronização e scheduler.

Não presumir que o suporte existente seja suficiente para o Vib-Ribbon.

Cada componente deve ser testado com o comportamento real do jogo.

Prioridade especial para CD-ROM, CDDA e SPU, pois a preservação das músicas oficiais é obrigatória.

## 4. BIOS

Começar utilizando a configuração recomendada pelo PSXRecomp e seu OpenBIOS, salvo incompatibilidade identificada.

A possibilidade de selecionar uma BIOS comercial compatível, obtida legalmente pelo usuário, pode ser disponibilizada como opção.

Não distribuir BIOS comercial.

Não implementar HLE como substituição silenciosa de funcionalidades necessárias à precisão do jogo.

## 5. ÁUDIO E MÚSICAS OFICIAIS

Preservar a infraestrutura original de áudio.

Investigar como o Vib-Ribbon acessa suas músicas e como as trilhas de áudio são organizadas na imagem do disco.

Não substituir o sistema original de reprodução por um player externo.

O sistema de músicas personalizadas deve ser independente e integrado através de uma interface de PC.

As músicas oficiais devem continuar funcionando pelo caminho original do jogo.

## 6. SISTEMA DE MÚSICAS PERSONALIZADAS

Criar uma camada de integração para músicas de PC.

Ela poderá utilizar FFmpeg, SDL3 e bibliotecas de análise musical, respeitando as interfaces e os componentes já existentes.

Não modificar desnecessariamente o runtime original.

O sistema deve transformar uma música personalizada em dados estruturados de eventos e obstáculos que possam ser consumidos pelo gameplay.

Investigar a melhor integração com a lógica original de geração de obstáculos antes de implementar qualquer substituição.

## 7. INSTRUMENTAÇÃO OBRIGATÓRIA

Criar um painel de diagnóstico de desenvolvimento que apresente:

- Quantidade de funções recompiladas.
- Cobertura de código estático.
- Overlays identificados.
- Overlays compilados nativamente.
- Overlays ainda não compilados.
- Chamadas ao interpretador.
- Falhas de despacho.
- Erros de runtime.
- Problemas de áudio.
- Problemas de sincronização.

Separar métricas de código estático, código dinâmico e execução pelo interpretador.

O painel não precisa aparecer na versão final distribuída, mas deve estar disponível durante o desenvolvimento.

## 8. TESTES DE FIDELIDADE

Comparar o funcionamento com uma referência legítima do jogo original.

Testar:

- Inicialização.
- Menus.
- Músicas.
- Obstáculos.
- Animações.
- Colisões.
- Pontuação.
- Progressão.
- Controles.
- Áudio.
- Sincronização.

Não confundir execução nativa com fidelidade.

Um programa pode ser nativo e ainda apresentar erros de compatibilidade.

## 9. REGRA FINAL

A arquitetura não pode ser substituída por um emulador convencional.

O runtime de hardware do PSXRecomp é permitido.

O código do jogo deve ser recompilado e executado nativamente sempre que tecnicamente possível.

O interpretador é uma contingência temporária e mensurável para código ainda não coberto, não uma solução para evitar o trabalho de recompilação.

Primeiro entregar um Vib-Ribbon original funcional.

Depois desenvolver as funcionalidades modernas de músicas personalizadas, editor de fases e biblioteca musical.

Não sacrificar a fidelidade do jogo original para acelerar funcionalidades secundárias.