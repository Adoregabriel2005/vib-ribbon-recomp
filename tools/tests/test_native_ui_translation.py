"""Compile the actual localization implementation, including UTF-8 and fallback."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('clang++'), 'clang++ is required')
class NativeTranslationTests(unittest.TestCase):
    def test_portuguese_accents_and_missing_key_fallback(self):
        temp_root = ROOT / '.cache' / 'tmp'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            folder = Path(folder)
            source = folder / 'translation.cpp'
            source.write_text('''#include "launcher_i18n.h"
#include <cstring>
int main() {
    if (std::strcmp(launcher_i18n_language(), "pt-BR")) return 1;
    if (std::strcmp(launcher_i18n_text("Settings"), "Configurações")) return 2;
    if (std::strcmp(launcher_i18n_text("Output device"), "Dispositivo de saída")) return 3;
    if (std::strcmp(launcher_i18n_text("untranslated##stable_id"), "untranslated##stable_id")) return 4;
    if (std::strcmp(launcher_i18n_text(nullptr), "")) return 5;
    return 0;
}
''', encoding='utf-8')
            common = ROOT / 'recomp-ui' / 'src' / 'common'
            exe = folder / 'translation.exe'
            subprocess.run(['clang++', '-std=c++17', '-DRECOMP_UI_LANGUAGE="pt-BR"',
                            '-I', str(common), str(source),
                            str(common / 'launcher_i18n.cpp'), '-o', str(exe)], check=True,
                           capture_output=True, text=True)
            subprocess.run([str(exe)], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
