# Validation status — November 12, 2026

This is an experimental Windows x64 build for the European SCES-02873 disc.
The detailed development log and local evidence references are preserved in
[the original Portuguese log](STATUS.md). Full reports and captures are not published.

## Observed in local tests

- OpenBIOS/LLE boot, language selection, original menus and entry into Round 1.
- Three overlay images with 28,335 audited dispatch variants. Variants are not
  unique functions or a percentage of executed native code. Fallback stays enabled.
- Manual MP3 gameplay and the original Auto mode using two user-provided MP3s.
  CDDA and host output produced nonzero audio; this does not establish audio fidelity.
- MP3 decoding uses a mapped source file. Both test songs produced PCM identical
  to the previous converter. Original tracks/files are left intact.
- PC settings include window/fullscreen, internal resolution, renderer, VSync
  and persistent volume. Not every live setting/controller path has been verified.
- The PC interface now supports English and Brazilian Portuguese, with a visible
  selector and persistent preference. The game's language is independent.
- Unit tests cover translation/fallback, saved language reload, invalid language
  values, patch application to pinned source, diagnostic framing and source checks.
  Native tests cover CD identification and FIFO/IRQ/DMA behavior.

## Still unverified

- Complete gameplay fidelity, timing, collision/score/progression and long sessions.
- Audio quality and audiovisual synchronization against an original reference.
  Previous accelerated-menu probes recorded underruns/drops; no clean-audio claim.
- End-of-track return, pause/resume and every manual/Demo transition.
- The official soundtrack Demo button and real physical/virtual CD hardware.
- Complete controller navigation, latency and every display option.
- Original game-text translation to Portuguese and full memory-card round trips.
- Full measured native coverage. Optional isolated AOT fragments remain disabled
  after a byte-audit failure; the audited base shard and fallback are retained.

CI runs without a ROM and does not build or play the complete game. There is no
stable public binary release. New language options require a rebuilt executable;
updating the README alone does not change an older launcher package.
