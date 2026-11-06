#include "config_loader.h"
#include <cassert>
#include <filesystem>
#include <fstream>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::filesystem::path path = argv[1];
    { std::ofstream out(path); out << "[audio]\nvolume=37\n[video]\nwindow_width=1600\nrenderer=\"opengl\"\n"; }
    auto settings = PSXRecompV4::load_user_settings(path);
    assert(settings.has_audio_volume && settings.audio_volume == 37);
    assert(settings.has_window_width && settings.window_width == 1600);
    assert(PSXRecompV4::save_user_settings(path, settings));
    auto restored = PSXRecompV4::load_user_settings(path);
    assert(restored.has_audio_volume && restored.audio_volume == 37);
    assert(restored.window_width == 1600 && restored.has_renderer && restored.renderer == 1);
    { std::ofstream out(path); out << "[audio]\nvolume=999\n[video]\nwindow_width=1600\n"; }
    auto invalid = PSXRecompV4::load_user_settings(path);
    assert(!invalid.has_audio_volume && invalid.window_width == 1600);
    std::filesystem::remove(path);
}
