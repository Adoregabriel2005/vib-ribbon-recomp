# Testing and contributing

Read README.md and docs/STATUS.en.md. Use your own European SCES-02873 dump.
When reporting a problem, include the commit/version, Windows version, CPU/GPU,
renderer, input device, reproduction steps and expected/observed behavior.
State whether it affects official music, MP3 or CD, and manual play or Demo.
For interface issues, include the selected language and the screen involved.

Do not attach ROMs, BIOS, music or personal saves. Review logs for personal paths
and share only the relevant excerpt. Full reports are ignored by Git.

Describe the problem and validation in your PR. Preserve OpenBIOS, REFERENCE/LLE
and the original audio path. Do not edit generated C to force progression or relax
byte guards. The interpreter is a fallback: code generation is not measured coverage.

Run the Python tests and tools/check_repository.py. Submodule changes require a
patch in patches/ so another checkout can reproduce them. Do not commit builds,
disc data or caches. Keep English and Brazilian Portuguese music-menu strings in
the shared localization table. The game-text language remains a separate setting.
