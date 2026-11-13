"""Compile the actual localization implementation, including UTF-8 and fallback."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import os

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
int main(int argc, char**) {
    if (argc > 2) {
        if (launcher_i18n_set_language("en")) return 30;
        return std::strcmp(launcher_i18n_language(), "en") ? 31 : 0;
    }
    if (argc > 1) {
        if (std::strcmp(launcher_i18n_language(), "en")) return 20;
        if (std::strcmp(launcher_i18n_text("Choose MP3 file..."), "Choose MP3 file...")) return 21;
        return 0;
    }
    if (std::strcmp(launcher_i18n_language(), "pt-BR")) return 1;
    if (std::strcmp(launcher_i18n_text("Settings"), "Configurações")) return 2;
    if (std::strcmp(launcher_i18n_text("Output device"), "Dispositivo de saída")) return 3;
    if (std::strcmp(launcher_i18n_text("untranslated##stable_id"), "untranslated##stable_id")) return 4;
    if (std::strcmp(launcher_i18n_text(nullptr), "")) return 5;
    if (std::strcmp(launcher_i18n_text("Choose MP3 file..."), "Escolher arquivo MP3...")) return 6;
    if (!launcher_i18n_set_language("en")) return 7;
    if (std::strcmp(launcher_i18n_text("Settings"), "Settings")) return 8;
    if (launcher_i18n_set_language("invalid")) return 9;
    if (std::strcmp(launcher_i18n_language(), "en")) return 10;
    return 0;
}
''', encoding='utf-8')
            common = ROOT / 'recomp-ui' / 'src' / 'common'
            exe = folder / 'translation.exe'
            subprocess.run(['clang++', '-std=c++17', '-DRECOMP_UI_LANGUAGE="pt-BR"',
                            '-I', str(common), str(source),
                            str(common / 'launcher_i18n.cpp'), '-o', str(exe)], check=True,
                           capture_output=True, text=True)
            preference = folder / 'language.txt'
            env = dict(os.environ, RECOMP_UI_LANGUAGE_FILE=str(preference))
            subprocess.run([str(exe)], check=True, capture_output=True, env=env)
            self.assertEqual(preference.read_text(encoding='utf-8'), 'en\n')
            subprocess.run([str(exe), 'restored'], check=True, capture_output=True, env=env)
            preference.write_text('not-a-language\n', encoding='utf-8')
            subprocess.run([str(exe)], check=True, capture_output=True, env=env)
            unwritable = dict(os.environ, RECOMP_UI_LANGUAGE_FILE=str(folder))
            subprocess.run([str(exe), 'save', 'fails'], check=True, capture_output=True, env=unwritable)


if __name__ == '__main__':
    unittest.main()
