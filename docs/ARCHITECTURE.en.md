# Architecture

The project's fixed architecture is native recompilation through PSXRecomp with
its compatible hardware runtime. Do not replace it with a conventional emulator.
The owner's original specification is preserved in [Portuguese](ARCHITECTURE.md).

## Execution and coverage

Extract the executable from the user's own disc, generate C from MIPS R3000A
code and compile it into the Windows runtime. Recompile identifiable static code
and dynamically loaded overlays using the framework's capture, cache and dispatch
services. Keep an instrumented interpreter fallback for uncovered code.

Separate generated functions, overlay variants, native dispatches and interpreted
instructions in reports. Record unknowns rather than inventing coverage. Never
relax byte guards or hand-edit generated game C to force progression.

## Hardware and fidelity

Reuse PSXRecomp's CPU/memory, BIOS, GPU/GTE, DMA/CD-ROM, CDDA/SPU, timers/IRQs,
controller and memory-card services. Start with OpenBIOS and retain the development
baseline: REFERENCE, LLE, bios_hle=false, hle_scheduler=false, 4:3 and native
resolution. Record evidence and reasons for compatibility-driven changes.

Preserve official music through the original CD-ROM/CDDA/SPU path. Custom MP3
music is decoded into a local audio CD consumed by the game's original analysis;
it is not played over an unrelated fixed level. Original user files remain intact.

Compare boot, program transitions, menus, obstacles, animation, collisions,
scoring, controls, audio and timing against a legitimate original reference.
Native execution alone is not proof of fidelity. Do not ship disc images or
commercial BIOS. Game-derived code and assets are generated locally.

## Modern interface

Use native PC menus for MP3/CD source selection, settings and Demo/manual choices.
Keep interface localization separate from original game-text language. English
and Brazilian Portuguese are selectable; original game text is not translated by
changing this preference. See the current limits in [STATUS](STATUS.en.md).
