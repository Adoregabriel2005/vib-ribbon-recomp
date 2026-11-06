"""Use the framework's bundler for capture -> native cache compilation."""
from pathlib import Path
import sys
import shutil
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'psxrecomp'))
import psxrecomp_cli as cli

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path, default=ROOT / 'build-runtime')
    args = parser.parse_args()
    result = cli.stage_overlay_toolchain_for_product(
        ROOT, args.runtime_dir.resolve(), cli.ProgressReporter())
    if result is None:
        raise SystemExit('Overlay toolchain staging failed; see framework output')
    compiler = shutil.which('gcc')
    if compiler:
        (Path(result) / 'compiler.txt').write_text(str(Path(compiler).resolve()) + '\n', encoding='utf-8')
        print('Local overlay compiler:', compiler)
