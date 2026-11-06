# Vib-Ribbon Recomp

Read `docs/ARCHITECTURE.md` and `docs/STATUS.md` before implementation.
Read `docs/PRODUCT-MENUS.md` for the owner's MP3/CD menus, native options,
Demo/manual modes and multilingual/PT-BR requirements. Preserve their scope
without reporting planned features as already implemented.
The user's fixed architecture is PSXRecomp native recompilation with its
hardware runtime. Do not replace the project with a conventional emulator.
Keep the interpreter as an instrumented fallback until native coverage is proven.

Original-game fidelity and official CD-ROM/CDDA/SPU playback come first.
Do not introduce an external music player for the official tracks.
Custom music, an editor and a library follow a validated original-game baseline.

Use the existing framework services and AOT tooling. Do not relax byte guards
or audits to admit a rejected native variant. Keep missing measurements unknown;
do not equate generated functions, dispatch variants and executed instructions.
Record known gaps and validation evidence in `docs/STATUS.md`.

Keep this development baseline on OpenBIOS, runtime `bios_hle = false`,
`hle_scheduler = false`, CMake REFERENCE/LLE, 4:3 and native resolution.
Any compatibility-driven change needs an explicit recorded reason and comparison.
Do not distribute disc images or commercial BIOS files.

Build with `scripts/build.ps1` (Python 3.11+, CMake, LLVM-MinGW and Make).
Use two compile jobs, one game probe, and private diagnostic saves for probes.
Do not hand-edit generated game C to force progression. Change verified inputs,
analysis or framework fixes with evidence, then regenerate.

The optional isolated-fragment AOT expansion is temporarily disabled after an
audit failure; see README and STATUS. The audited three-image shard is linked.
Do not report full coverage or a playable port without runtime/fidelity evidence.
