# Vib-Ribbon Recomp

[Português (Brasil)](README.pt-BR.md)

Experimental Windows x64 port of the European **SCES-02873** version of
Vib-Ribbon, built with [PSXRecomp](https://github.com/RetroPortingToolKit/psxrecomp)
and its hardware runtime. Execution combines recompiled code, native overlays
and an instrumented interpreter fallback. Full fidelity and 100% native coverage
have not been established.

## Tested features

- OpenBIOS/LLE boot, original menus and entry into gameplay.
- An MP3 menu integrated with the original custom-CD option, with **Play** and
  **Watch (Demo)**. The game analyzes the music and generates its own obstacles.
- **English and Brazilian Portuguese** PC interfaces. Use **Language / Idioma**
  at the top of the launcher or the F10 music menu. Changes apply immediately
  and are saved beside the executable in `interface-language.txt`.
- PC volume, window/fullscreen, internal resolution, renderer and VSync settings.
  Some changes require a restart. Original sound/vibration options remain available.

New builds default to English. The game's own language selection is separate;
changing the PC interface does not translate the original game text.

**Still experimental:** audio quality/synchronization, end-of-track transitions,
pause/resume, full controller navigation and long sessions. Physical/virtual CD
support is implemented but has not been verified with a real device. The official
soundtrack Demo button still needs testing. See [status](docs/STATUS.en.md).

## Build on Windows

Install Git, Python 3.11+, CMake, LLVM-MinGW/Clang, `mingw32-make` and `gcc` on
PATH. Use PowerShell. Builds use two compile jobs at a time.

```powershell
git clone --recurse-submodules --shallow-submodules https://github.com/Adoregabriel2005/vib-ribbon-recomp.git
cd vib-ribbon-recomp
./scripts/setup.ps1
./scripts/build.ps1 -NativeUI -Disc 'D:\Games\Vib-Ribbon (Europe) (En,Fr,De,Es,It).cue'
./scripts/run.ps1 -NativeUI
```

Provide your own European disc dump, with its CUE and **all eight track BINs**
together. Setup verifies the data-track hash, extracts the boot locally and
stores your private disc path in `game.local.toml`, which Git ignores. Original
tracks are neither changed nor duplicated. Game-derived C is generated locally
in `generated/`. The first build downloads dependencies and may take a while.

Submodules are pinned in [framework_pins.txt](framework_pins.txt). Setup applies
the local patches once and stops on conflicts, preserving local changes.
After code generation, rebuild with:

```powershell
./scripts/build.ps1 -NativeUI -SkipGenerate
```

If Python is not detected, add `-Python 'C:\path\to\python.exe'` to the build
command. Compile with `-NativeUI -Diagnostics` to enable developer probes.

## Load a custom MP3

1. Enter the original custom-CD option, or press **F10** / **Ctrl+L**.
2. Select **Choose MP3 file...** and choose your MP3.
3. Wait for **Music ready.** Then select **Play this music** or **Watch this music (Demo)**.
4. In the game, confirm **Single track** (or **All tracks**) and track **1**.

If the interface is in Portuguese, use **Language / Idioma → English** first.
This selector is visible in both the launcher and music menu.

The prepared audio in `build-native-ui/music-cache` feeds the original
CD-ROM/CDDA/SPU path; it is not an external player layered over a fixed level.
The cache uses about 10.6 MB per minute and does not yet clean itself automatically.
Do not remove the active prepared track. Your source MP3 remains unchanged.
Official music still uses the game disc. The development baseline is 4:3, native
resolution, REFERENCE and LLE; graphical enhancements are optional.

## Tests and bug reports

```powershell
python -m unittest discover -s tools/tests -v
python tools/check_repository.py
```

Probes use private saves and stop only their own process. Full logs, captures
and caches stay local. CI checks tools, localization, patches and CD regressions
without a ROM; passing CI does not establish gameplay fidelity.
See [CONTRIBUTING](CONTRIBUTING.md) before opening an issue.

This repository contains no ROMs, music tracks, commercial BIOS, original game
executables or generated game C. There is no stable binary release yet.

## Credits

Independent project, unaffiliated with the owners of Vib-Ribbon.
PSXRecomp uses PolyForm Noncommercial 1.0.0; dependencies retain their own licenses.
See [THIRD_PARTY](THIRD_PARTY.md) and [architecture](docs/ARCHITECTURE.en.md).
