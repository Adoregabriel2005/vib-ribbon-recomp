# Vib-Ribbon Recomp

[English](README.md)

Port experimental para Windows x64 do Vib-Ribbon europeu **SCES-02873**, usando
[PSXRecomp](https://github.com/RetroPortingToolKit/psxrecomp) e seu runtime.
Combina código recompilado, overlays nativos e fallback instrumentado.
Fidelidade completa e 100% de cobertura ainda não foram comprovadas.

## Disponível nos testes

- Boot OpenBIOS/LLE, menus originais e entrada em partidas.
- Menu MP3 integrado a opção de CD próprio, com **Jogar** e **Assistir (Demo)**.
  O jogo analisa o áudio e gera os próprios obstáculos, sem player sobreposto.
- Interface PC em inglês e PT-BR: volume, janela/tela cheia, resolução interna,
  renderizador e VSync. Algumas alterações exigem reiniciar.
- Acesso as opções originais de som/vibracao e as músicas oficiais.

**Experimental:** áudio/sincronização, fim de faixa, pausa/retomada, controle e
estabilidade prolongada. CD físico/virtual tem backend implementado, ainda sem
validação com dispositivo real. PT-BR cobre a interface PC; textos do jogo
permanecem originais. Demo das faixas oficiais ainda precisa de teste.
Veja [STATUS](docs/STATUS.md) e [requisitos](docs/PRODUCT-MENUS.md).

## Compilar no Windows

Instale Git, Python 3.11+, CMake, LLVM-MinGW/Clang, mingw32-make e gcc no PATH.
Use PowerShell. O build usa dois processos de compilação por vez.

```powershell
git clone --recurse-submodules --shallow-submodules https://github.com/Adoregabriel2005/vib-ribbon-recomp.git
cd vib-ribbon-recomp
./scripts/setup.ps1
./scripts/build.ps1 -NativeUI -Disc 'D:\Jogos\Vib-Ribbon (Europe) (En,Fr,De,Es,It).cue'
./scripts/run.ps1 -NativeUI
```

Use seu próprio dump europeu: CUE e **todas as oito faixas BIN** juntas.
O preparo valida o hash, extrai o boot localmente e salva o caminho privado em
`game.local.toml`, ignorado pelo Git. Nao altera nem duplica as faixas originais.
O código do disco e gerado localmente em `generated/`.
O primeiro build baixa dependências e pode levar vários minutos.

Submódulos fixados em [framework_pins.txt](framework_pins.txt). O setup aplica
patches uma vez e interrompe em conflitos, preservando alterações locais.
Para recompilar depois: `./scripts/build.ps1 -NativeUI -SkipGenerate`.

## Testar músicas

Use **Language / Idioma** no topo do launcher ou menu F10 para selecionar
**English** ou **Português (Brasil)**. A escolha é salva em
`interface-language.txt`, ao lado do executável. Novas instalações começam em
inglês; o idioma dos textos originais do jogo continua separado.

1. Entre na opção de CD próprio ou pressione **F10** / **Ctrl+L**.
2. Escolha um MP3, aguarde e selecione **Jogar** ou **Assistir (Demo)**.
3. No jogo, confirme **Single track** ou **All tracks** e a faixa **1**.

O cache em `build-native-ui/music-cache` alimenta o caminho CD-ROM/CDDA/SPU.
Ocupa aproximadamente 10,6 MB por minuto e ainda não tem limpeza automática.
Nao remova a faixa preparada enquanto estiver em uso. Originais ficam intactos.
Musicas oficiais continuam pelo disco do jogo. Padrão: 4:3, resolução nativa,
REFERENCE e LLE; melhorias gráficas são opcionais.

## Testes e contribuições

```powershell
python -m unittest discover -s tools/tests -v
python tools/check_repository.py
```

Diagnóstico do jogo: compile com `-NativeUI -Diagnostics`. Probes usam saves
próprios e encerram apenas o processo iniciado. Relatórios, capturas e caches
ficam locais. A CI testa ferramentas e tradução sem ROM; não comprova gameplay.
Veja [CONTRIBUTING](CONTRIBUTING.md) para reportar problemas.

Este repositório não inclui ROMs, músicas, BIOS comerciais, executaveis originais
ou C gerado do disco. Nao há release estável publicada.

## Créditos

Projeto independente, sem afiliação com os titulares de Vib-Ribbon.
PSXRecomp usa PolyForm Noncommercial 1.0.0; dependências preservam suas licenças.
Veja [THIRD_PARTY](THIRD_PARTY.md).
