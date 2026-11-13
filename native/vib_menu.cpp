#include "music_disc.h"
#include "psx_menu_host.h"
#include "recomp_ui_psx_menu.h"
#include "cdrom.h"
#include "psx_disc_tray.h"
#include "iso_reader.h"
#include "mod_plugins.h"
#include "func_override.h"
#include "cpu_state.h"
#include "host_osd.h"
#include "config_loader.h"
#include "internal_resolution.h"
#include "launcher_i18n.h"
#include <SDL3/SDL.h>
#include "imgui.h"
#include "imgui_impl_sdl3.h"
#include "imgui_impl_opengl3.h"
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <commdlg.h>
#include <atomic>
#include <chrono>
#include <future>
#include <mutex>
#include <string>
#include <vector>
#include <cstdio>
#include <cstring>

namespace {
const char* tr(const char* english) { return launcher_i18n_text(english); }
bool portuguese() { return std::strcmp(launcher_i18n_language(), "pt-BR") == 0; }
const PsxMenuHost* host;
PsxMenuHost settings_host{};
const PsxMenuProvider* settings;
SDL_Window* window;
ImGuiContext* context;
std::mutex mutex;
std::atomic<bool> opened{false};
std::atomic<int> pending{-1};
Uint32 action_event, done_event;
int page, selection;
bool busy;
uint32_t pad_buttons;
std::string status, boot_disc;
std::string queued_file;
std::vector<char> drives;
std::future<vib::MusicDisc> conversion;
vib::MusicDisc prepared;
std::string queued_media;
std::atomic<bool> media_armed{false}, official_demo{false};
std::atomic<int> mode_request{-1}, game_scene{0};
std::atomic<int> active_music_mode{-1};
uint32_t previous_scene;
bool demo_choice;
PsxHostVideoSettings pc_video{};
int pc_width = 960, pc_volume = 100, pc_resolution = 1, pc_vsync = 1;
bool pc_auto_resolution, pc_resolution_changed;
bool settings_from_game;
bool post_action(int action);
#ifndef PSX_NO_DEBUG_TOOLS
std::atomic<uint32_t> scene_words[36];
#endif
int set_mode(CPUState* cpu) {
    if (cpu->gpr[28] != 0x80075E24u) return 0;
    if (host && host->netplay_active && host->netplay_active()) return 0;
    if (cpu->gpr[4] <= 2 && official_demo.exchange(false)) {
        cpu->gpr[4] += 5; // The original setter marks official demo modes 5..7.
        func_override_call_original(cpu);
        return 1;
    }
    const uint32_t original = cpu->gpr[4];
    const int requested = active_music_mode.load();
    if (requested >= 0 && (original == 3 || original == 4 || original == 8)) {
        const uint32_t mode = requested ? 8u : original == 8 ? 3u : original;
        if (mode != original) {
            // The session driver also reads its own mode, not only the menu copy.
            if (cpu->read_word(cpu->gpr[28] + 0x840u) == original)
                cpu->write_word(cpu->gpr[28] + 0x840u, mode);
            cpu->gpr[4] = mode;
            func_override_call_original(cpu);
            return 1;
        }
    }
    return 0;
}
int observe_menu(CPUState* cpu) {
    func_override_call_original(cpu);
    const uint32_t gp = cpu->gpr[28];
    if (gp == 0x80075E24u) {
        const uint32_t scene = cpu->read_word(gp + 0x5A0u);
        game_scene = static_cast<int>(scene);
        if (host && !(host->netplay_active && host->netplay_active())) {
            if (scene == 8) {
                const int requested = mode_request.exchange(-1);
                if (requested >= 0 && cpu->read_word(0x8003FE54u) == 0xAF840580u &&
                    cpu->read_word(0x8003FE60u) == 0xAF840584u) {
                    const uint32_t old_mode = cpu->read_word(gp + 0x580u);
                    const uint32_t mode = requested ? 8u : old_mode == 4 ? 4u : 3u;
                    // Exact data contract of the byte-verified original mode setter.
                    cpu->write_word(gp + 0x580u, mode);
                    cpu->write_word(gp + 0x584u, 0);
                    const uint32_t session_mode = cpu->read_word(gp + 0x840u);
                    if (session_mode == 3 || session_mode == 4 || session_mode == 8)
                        cpu->write_word(gp + 0x840u, mode);
                }
                if (media_armed && post_action(11)) media_armed = false;
                else if (scene != previous_scene && !media_armed) post_action(12);
            } else if (scene == 3 && scene != previous_scene) post_action(12);
            else if (scene == 10 && scene != previous_scene) post_action(13);
        }
        previous_scene = scene;
#ifndef PSX_NO_DEBUG_TOOLS
        for (int i = 0; i < 36; ++i) scene_words[i] = cpu->read_word(gp + 0x540u + i * 4u);
#endif
    }
    return 1;
}

void show(bool on) {
    if (!host) return;
    if (on && host->netplay_active && host->netplay_active()) return;
    opened = on;
    if (host->set_paused) host->set_paused(on ? 1 : 0);
    if (on) { selection = 0; page = 0; }
}

bool post_action(int action) {
    int empty = -1;
    if (!pending.compare_exchange_strong(empty, action)) return false;
    SDL_Event event{}; event.type = action_event;
    if (!SDL_PushEvent(&event)) { pending = -1; return false; }
    return true;
}

std::filesystem::path choose(bool mp3) {
    wchar_t file[32768]{};
    OPENFILENAMEW dialog{};
    dialog.lStructSize = sizeof dialog;
    dialog.hwndOwner = static_cast<HWND>(SDL_GetPointerProperty(
        SDL_GetWindowProperties(window), SDL_PROP_WINDOW_WIN32_HWND_POINTER, nullptr));
    dialog.lpstrFilter = mp3 ? L"MP3\0*.mp3\0\0" : L"CD image (CUE)\0*.cue\0\0";
    dialog.lpstrFile = file;
    dialog.nMaxFile = sizeof file / sizeof file[0];
    dialog.lpstrTitle = portuguese() ? (mp3 ? L"Escolher música MP3" : L"Escolher CD de áudio") :
        (mp3 ? L"Choose MP3 file" : L"Choose audio CD");
    dialog.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR;
    if (!GetOpenFileNameW(&dialog)) return {};
    return std::filesystem::path(file);
}

bool mount(const std::string& path) {
    if (!host || (host->netplay_active && host->netplay_active())) return false;
    PS1::ISOReader check;
    if (!check.Open(path)) { status = "Could not read this CD. Check the disc and drive."; return false; }
    bool audio = false;
    for (int i = 1; i <= check.TrackCount(); ++i) audio |= check.TrackIsAudio(i);
    if (!audio) { status = "This disc has no audio tracks."; return false; }
    check.Close();
    if (boot_disc.empty()) {
        if (const char* original = cdrom_mounted_path()) boot_disc = original;
    }
    if (boot_disc.empty()) { status = "The original disc is not ready yet."; return false; }
    // Keep the game's boot image at index 1; music exists only in this session.
    const int old = cdrom_disc_selected();
    const char* paths[] = {boot_disc.c_str(), path.c_str()};
    cdrom_disc_roster_set(paths, 2, old == 2 ? 2 : 1);
    if (psx_disc_tray_cycle(2, PSX_DISC_TRAY_ORIGIN_SESSION_MUSIC) != PSX_DISC_TRAY_OK) {
        status = "Could not insert the CD. Try another music source.";
        return false;
    }
    status = "Music inserted. Choose the track in the game menu.";
    show(false);
    return true;
}

void choose_media(const std::string& path, bool demo) {
    queued_media = path;
    demo_choice = demo;
    mode_request = demo ? 1 : 0;
    active_music_mode = demo ? 1 : 0;
    official_demo = false;
    media_armed = true;
    if (game_scene == 8) {
        // Let the guarded guest-menu boundary apply the mode before mounting.
        show(false);
    } else {
        status = "Music ready. Choose Single track or All tracks in the game, then track 1.";
        host_osd_push(tr(status.c_str()), 5000);
        show(false);
    }
}

void pc_settings() {
    host->video_get(&pc_video);
    int height = 0; SDL_GetWindowSize(window, &pc_width, &height);
    pc_volume = host_volume_get();
    pc_auto_resolution = pc_video.internal_resolution == PSX_IR_AUTO;
    pc_resolution = pc_auto_resolution ? 1 : pc_video.internal_resolution;
    pc_resolution_changed = false;
    auto path = std::filesystem::u8path(SDL_GetBasePath()) / "settings.toml";
    const auto saved = PSXRecompV4::load_user_settings(path);
    const int vsync = saved.has_vsync ? saved.vsync : 1;
    pc_vsync = vsync == -1 ? 2 : vsync == 2 ? 3 : vsync;
    page = 2;
}

void apply_pc_settings() {
    const auto path = std::filesystem::u8path(SDL_GetBasePath()) / "settings.toml";
    auto saved = PSXRecompV4::load_user_settings(path);
    if (saved.parse_error) { status = "The settings file contains an error and was preserved."; return; }
    const int vsync = pc_vsync == 2 ? -1 : pc_vsync == 3 ? 2 : pc_vsync;
    const bool restart_sync = (saved.has_vsync ? saved.vsync : 1) != vsync;
    saved.window_width = pc_width; saved.has_window_width = true;
    saved.audio_volume = pc_volume; saved.has_audio_volume = true;
    saved.vsync = vsync; saved.has_vsync = true;
    if (!PSXRecompV4::save_user_settings(path, saved)) { status = "Could not save settings."; return; }
    host_volume_set(pc_volume);
    SDL_SetWindowSize(window, pc_width, pc_width * 3 / 4);
    const unsigned restart_video = host->video_apply(&pc_video);
    if (pc_resolution_changed && host->mod_set) {
        const char* package = "psx.enhancement.internal-resolution";
        const std::string resolution = pc_auto_resolution ? "auto" : std::to_string(pc_resolution) + 'x';
        host->mod_set(package, "internal-resolution", "resolution", resolution.c_str());
        host->mod_set(package, "internal-resolution", nullptr,
            pc_auto_resolution || pc_resolution != 1 ? "true" : "false");
    }
    status = restart_video || restart_sync ?
        "Settings saved. Restart to apply renderer or VSync changes." :
        "Settings applied and saved.";
}

void act(int action) {
    if (!host) return;
    if (action == 0) { show(false); return; }
    if ((action == 1 || action == 9) && !busy) {
        auto source = action == 9 ? std::filesystem::u8path(queued_file) : choose(true);
        if (source.empty()) return;
        busy = true;
        prepared = {};
        status = "Preparing music...";
        const auto cache = std::filesystem::u8path(SDL_GetBasePath()) / "music-cache";
        conversion = std::async(std::launch::async, [source, cache]() {
            try { auto result = vib::prepare_mp3(source, cache);
                SDL_Event e{}; e.type = done_event; SDL_PushEvent(&e); return result;
            } catch (...) { SDL_Event e{}; e.type = done_event; SDL_PushEvent(&e); throw; }
        });
    } else if (action == 2) {
        page = 1; selection = 0; drives.clear();
        const DWORD mask = GetLogicalDrives();
        for (char letter = 'A'; letter <= 'Z'; ++letter) {
            if (!(mask & (1u << (letter - 'A')))) continue;
            wchar_t root[] = L"D:\\"; root[0] = letter;
            if (GetDriveTypeW(root) == DRIVE_CDROM) drives.push_back(letter);
        }
        if (drives.empty()) status = "No physical or virtual CD drive was found.";
    } else if (action == 3) {
        auto file = choose(false);
        if (!file.empty()) choose_media(file.u8string(), demo_choice);
    } else if (action == 4) {
        settings_from_game = false;
        pc_settings();
    } else if (action == 5) {
        media_armed = false; official_demo = false; mode_request = -1; active_music_mode = -1;
        if (boot_disc.empty()) return;
        const int requested = cdrom_disc_roster_count() > 1 ? 1 : 0;
        if (psx_disc_tray_cycle(requested, PSX_DISC_TRAY_ORIGIN_SESSION_MUSIC) == PSX_DISC_TRAY_OK) {
            status = "Vib-Ribbon disc inserted."; show(false);
        }
        else status = "Could not read the game disc again.";
    } else if ((action == 6 || action == 14) && !prepared.cue.empty())
        choose_media(prepared.cue.u8string(), action == 14);
    else if (action == 7) {
        if (page == 2 && settings_from_game) show(false);
        else { page = 0; selection = 0; }
    }
    else if (action == 11) { if (!mount(queued_media)) show(true); }
    else if (action == 12) show(true);
    else if (action == 13) { show(true); settings_from_game = true; pc_settings(); }
    else if (action == 15) {
        if (game_scene != 1 && game_scene != 2) {
            status = "Return to the GAME menu to choose music from the original disc."; return;
        }
        if (cdrom_disc_roster_count() > 1 && cdrom_disc_selected() != 1)
            psx_disc_tray_cycle(1, PSX_DISC_TRAY_ORIGIN_SESSION_MUSIC);
        active_music_mode = -1; official_demo = true; show(false);
        host_osd_push(tr("Demo: choose a difficulty for the game disc."), 5000);
    }
    else if (action == 20) apply_pc_settings();
    else if (action == 21) { show(false); settings->set_open(settings->ctx, 1); }
    else if (action >= 100 && action - 100 < static_cast<int>(drives.size())) {
        std::string uri = "cdda://"; uri += drives[action - 100]; uri += ':'; choose_media(uri, demo_choice);
    }
}

int attach(void*, void* sdl_window, void* gl, const PsxMenuHost* value) {
    std::lock_guard<std::mutex> guard(mutex);
    host = value; window = static_cast<SDL_Window*>(sdl_window);
    settings = recomp_ui_psx_menu_provider();
    settings_host = *host; settings_host.default_selection = 0;
    if (!settings->attach(settings->ctx, sdl_window, gl, &settings_host)) { host = nullptr; return 0; }
    if (const char* path = cdrom_mounted_path()) {
        if (cdrom_disc_roster_count() < 2 || boot_disc.empty()) boot_disc = path;
    }
    action_event = SDL_RegisterEvents(2); done_event = action_event + 1;
    if (action_event == 0) { settings->detach(settings->ctx); host = nullptr; return 0; }
    auto* previous = ImGui::GetCurrentContext();
    context = ImGui::CreateContext(); ImGui::SetCurrentContext(context);
    ImGui::GetIO().IniFilename = nullptr;
    ImFontConfig font{}; font.SizePixels = 19;
    ImGui::GetIO().Fonts->AddFontDefault(&font);
    ImGui::GetIO().ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard | ImGuiConfigFlags_NavEnableGamepad;
    ImGui::GetStyle().WindowRounding = 18;
    ImGui::GetStyle().FrameRounding = 14;
    ImGui::GetStyle().FrameBorderSize = 1;
    ImGui::GetStyle().Colors[ImGuiCol_WindowBg] = ImVec4(0,0,0,0.97f);
    ImGui::GetStyle().Colors[ImGuiCol_Button] = ImVec4(0.04f,0.04f,0.04f,1);
    ImGui::GetStyle().Colors[ImGuiCol_ButtonHovered] = ImVec4(0.2f,0.2f,0.2f,1);
    ImGui::GetStyle().Colors[ImGuiCol_ButtonActive] = ImVec4(0.35f,0.35f,0.35f,1);
    ImGui::GetStyle().Colors[ImGuiCol_Border] = ImVec4(1,1,1,1);
    ImGui::GetStyle().Colors[ImGuiCol_TitleBg] = ImVec4(0.02f,0.02f,0.02f,1);
    ImGui::GetStyle().Colors[ImGuiCol_TitleBgActive] = ImVec4(0.05f,0.05f,0.05f,1);
    ImGui::GetStyle().Colors[ImGuiCol_CheckMark] = ImVec4(1,1,1,1);
    ImGui::GetStyle().Colors[ImGuiCol_SliderGrab] = ImVec4(0.7f,0.7f,0.7f,1);
    ImGui::GetStyle().Colors[ImGuiCol_SliderGrabActive] = ImVec4(0.9f,0.9f,0.9f,1);
    const bool ok = ImGui_ImplSDL3_InitForOpenGL(window, gl) && ImGui_ImplOpenGL3_Init(nullptr);
    ImGui::SetCurrentContext(previous);
    return ok ? 1 : 0;
}

int event(void*, const void* raw) {
    std::lock_guard<std::mutex> guard(mutex);
    const auto& e = *static_cast<const SDL_Event*>(raw);
    if (e.type == action_event) {
        try { act(pending.exchange(-1)); }
        catch (const std::exception& error) { status = error.what(); show(true); }
        return 1;
    }
    if (e.type == done_event) {
        if (busy && conversion.valid()) {
            try { prepared = conversion.get(); status = "Music ready."; }
            catch (const std::exception& ex) { status = ex.what(); }
            busy = false;
        }
        return 1;
    }
    if (e.type == SDL_EVENT_KEY_DOWN && !e.key.repeat &&
        (e.key.key == SDLK_F10 || (e.key.key == SDLK_L && (e.key.mod & SDL_KMOD_CTRL)))) {
        if (settings->is_open(settings->ctx)) settings->set_open(settings->ctx, 0);
        show(!opened); return 1;
    }
    if (e.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN || e.type == SDL_EVENT_GAMEPAD_BUTTON_UP) {
        const uint32_t combo = (1u << SDL_GAMEPAD_BUTTON_BACK) | (1u << SDL_GAMEPAD_BUTTON_LEFT_STICK);
        const uint32_t before = pad_buttons;
        const uint32_t bit = 1u << e.gbutton.button;
        if (e.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN) pad_buttons |= bit; else pad_buttons &= ~bit;
        if ((pad_buttons & combo) == combo && (before & combo) != combo) {
            settings->set_open(settings->ctx, 0); show(!opened); return 1;
        }
    }
    if (!opened) return settings->event(settings->ctx, raw);
    if (e.type == SDL_EVENT_KEY_DOWN && e.key.key == SDLK_ESCAPE) {
        if (page == 2 && settings_from_game) show(false);
        else if (page) { page = 0; selection = 0; } else show(false);
        return 1;
    }
    if (e.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN && e.gbutton.button == SDL_GAMEPAD_BUTTON_EAST) {
        if (page == 2 && settings_from_game) show(false);
        else if (page) { page = 0; selection = 0; } else show(false);
        return 1;
    }
    auto* previous = ImGui::GetCurrentContext(); ImGui::SetCurrentContext(context);
    ImGui_ImplSDL3_ProcessEvent(&e); ImGui::SetCurrentContext(previous);
    switch (e.type) {
    case SDL_EVENT_KEY_DOWN: case SDL_EVENT_KEY_UP: case SDL_EVENT_TEXT_INPUT:
    case SDL_EVENT_MOUSE_MOTION: case SDL_EVENT_MOUSE_BUTTON_DOWN: case SDL_EVENT_MOUSE_BUTTON_UP:
    case SDL_EVENT_MOUSE_WHEEL: case SDL_EVENT_GAMEPAD_BUTTON_DOWN:
    case SDL_EVENT_GAMEPAD_BUTTON_UP: case SDL_EVENT_GAMEPAD_AXIS_MOTION: return 1;
    default: return 0; // The host still owns window changes and device arrival/removal.
    }
}

void draw(void*, int w, int h) {
    std::lock_guard<std::mutex> guard(mutex);
    if (!opened) { settings->draw(settings->ctx, w, h); return; }
    auto* previous = ImGui::GetCurrentContext(); ImGui::SetCurrentContext(context);
    ImGui_ImplOpenGL3_NewFrame(); ImGui_ImplSDL3_NewFrame(); ImGui::NewFrame();
    const auto size = ImGui::GetIO().DisplaySize;
    const float width = size.x < 660 ? size.x - 20 : 640;
    ImGui::SetNextWindowSizeConstraints(ImVec2(200, 0), ImVec2(width, size.y - 20));
    ImGui::SetNextWindowSize(ImVec2(width, 0));
    ImGui::SetNextWindowPos(ImVec2(size.x/2, size.y/2), ImGuiCond_Always, ImVec2(0.5f,0.5f));
    ImGui::Begin("Vib-Ribbon##vib_music", nullptr,
        ImGuiWindowFlags_AlwaysAutoResize | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoMove);
    int language = portuguese() ? 1 : 0;
    ImGui::SetNextItemWidth(230);
    if (ImGui::Combo("Language / Idioma##music_language", &language, "English\0Português (Brasil)\0")) {
        if (!launcher_i18n_set_language(language ? "pt-BR" : "en"))
            status = "Language changed for this session, but could not be saved.";
    }
    ImGui::TextUnformatted(tr(page == 2 ? "PC settings" : page == 1 ? "Audio CD" : "My music"));
    ImGui::Separator();
    if (page != 2) ImGui::TextWrapped("%s", tr("Choose an MP3, wait for preparation, then select Play or Demo. In the game, confirm Single track and track 1."));
    auto button = [&](const char* text, int id, bool enabled = true) {
        if (!enabled) ImGui::BeginDisabled();
        if (ImGui::Button(tr(text), ImVec2(-1, 34))) post_action(id);
        if (!enabled) ImGui::EndDisabled();
    };
    if (!page) {
        button("Resume game", 0);
        button("Choose MP3 file...", 1, !busy);
        if (!prepared.cue.empty()) {
            button("Play this music", 6, !busy);
            button("Watch this music (Demo)", 14, !busy);
        }
        button("Physical or virtual CD drive...", 2, !busy);
        button("Open CD image (CUE)...", 3, !busy);
        button("PC settings", 4);
        button("Watch game music (Demo)", 15, !busy && (game_scene == 1 || game_scene == 2));
        button("Reinsert Vib-Ribbon disc", 5, !busy);
    } else if (page == 1) {
        if (ImGui::RadioButton(tr("Play"), !demo_choice)) demo_choice = false;
        ImGui::SameLine();
        if (ImGui::RadioButton(tr("Watch / Demo"), demo_choice)) demo_choice = true;
        for (size_t i = 0; i < drives.size(); ++i) {
            std::string label = "Drive "; label += drives[i]; label += ':';
            button(label.c_str(), 100 + static_cast<int>(i));
        }
        button("Refresh drives", 2);
        button("Back", 7);
    } else {
        ImGui::SliderInt(tr("Window width"), &pc_width, 640, 3840, "%d px");
        ImGui::Combo(tr("Fullscreen"), &pc_video.fullscreen, portuguese() ? "Janela\0Sem bordas\0Exclusiva\0" : "Windowed\0Borderless\0Exclusive\0");
        ImGui::Combo(tr("Renderer"), &pc_video.renderer, "Software\0OpenGL\0");
        pc_resolution_changed |= ImGui::Checkbox(tr("Automatic internal resolution"), &pc_auto_resolution);
        if (pc_auto_resolution) ImGui::BeginDisabled();
        pc_resolution_changed |= ImGui::SliderInt(tr("Internal resolution"), &pc_resolution, 1, 32, "%dx");
        if (pc_auto_resolution) ImGui::EndDisabled();
        ImGui::Combo("VSync", &pc_vsync, portuguese() ? "Desligado\0Ligado\0Adaptativo\0VRR\0" : "Off\0On\0Adaptive\0VRR\0");
        ImGui::SliderInt(tr("Volume"), &pc_volume, 0, 100, "%d%%");
        ImGui::TextWrapped("%s", tr("Renderer and VSync may require a restart. Game speed stays unchanged."));
        button("Apply and save", 20);
        button("More session settings", 21);
        button("Back", 7);
    }
    if (busy) ImGui::TextUnformatted(tr("Preparing music..."));
    if (!status.empty()) { ImGui::Separator(); ImGui::TextWrapped("%s", tr(status.c_str())); }
    if (page != 2 && !prepared.cue.empty()) {
        ImGui::TextWrapped("%s", prepared.title.c_str());
        ImGui::Text(tr("Duration: %.1f s"), prepared.seconds());
    }
    ImGui::TextUnformatted(tr("F10 / Ctrl+L: menu     Esc: back"));
    ImGui::End(); ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
    ImGui::SetCurrentContext(previous);
}

int is_open(void*) { return opened || (settings && settings->is_open(settings->ctx)); }
void set_open(void*, int on) {
    std::lock_guard<std::mutex> guard(mutex);
    if (settings) settings->set_open(settings->ctx, 0);
    show(on != 0);
}
void detach(void*) {
    std::lock_guard<std::mutex> guard(mutex);
    if (conversion.valid()) { conversion.wait(); try { (void)conversion.get(); } catch (...) {} }
    busy = false; pending = -1; show(false);
    auto* previous = ImGui::GetCurrentContext(); ImGui::SetCurrentContext(context);
    ImGui_ImplOpenGL3_Shutdown(); ImGui_ImplSDL3_Shutdown(); ImGui::DestroyContext(context);
    ImGui::SetCurrentContext(previous == context ? nullptr : previous); context = nullptr;
    settings->detach(settings->ctx); host = nullptr;
}
PsxMenuProvider provider{PSX_MENU_ABI_VERSION, "Vib-Ribbon music and settings", nullptr,
    attach, event, is_open, set_open, draw, detach};
#ifndef PSX_NO_DEBUG_TOOLS
int debug_music(const char* args, char* reply, int cap) {
    try {
        std::lock_guard<std::mutex> guard(mutex);
        const std::string command = args ? args : "";
        if (command == "scene") {
            int written = 0;
            for (int i = 0; i < 36 && written + 18 < cap; ++i)
                written += std::snprintf(reply + written, cap - written, "%03X:%08X ",
                    0x540 + i * 4, scene_words[i].load());
            return 1;
        }
        if (command.rfind("language ", 0) == 0) {
            if (!launcher_i18n_set_language(command.c_str() + 9)) {
                std::snprintf(reply, cap, "language change could not be saved"); return 0;
            }
        }
        if (command.rfind("prepare ", 0) == 0 && host && !busy) {
            queued_file = command.substr(8); post_action(9);
        } else if (command == "insert" && host) post_action(6);
        else if (command == "demo" && host) post_action(14);
        else if (command == "official-demo" && host) post_action(15);
        else if (command == "settings" && host) post_action(4);
        else if (command == "drives" && host) post_action(2);
        else if (command == "original" && host) post_action(5);
        else if (command == "open" && host) show(true);
        else if (command == "close" && host) post_action(0);
        std::snprintf(reply, cap, "attached=%d busy=%d prepared=%d open=%d scene=%d mode=%d drives=%zu volume=%d language=%s status=%s",
            host != nullptr, busy, !prepared.cue.empty(), opened.load(), game_scene.load(),
            active_music_mode.load(), drives.size(), host_volume_get(), launcher_i18n_language(), status.c_str());
        return 1;
    } catch (...) { std::snprintf(reply, cap, "request failed"); return 0; }
}
#endif
struct Register { Register() {
    psx_menu_set_provider(&provider);
#ifndef PSX_NO_DEBUG_TOOLS
    psx_mod_register_command("vib.music", debug_music);
#endif
    const uint32_t guard[] = {0x8F8405B8u, 0x27BDFFE8u, 0xAFBF0014u, 0x0C00B79Cu};
    func_override_add_guarded("vib.menu.observe", 0x8003FBC0u, observe_menu, guard, 4, FO_CREDIT_SELF);
    const uint32_t mode_guard[] = {0xAF840580u, 0x2484FFFBu, 0x2C840003u, 0xAF840584u};
    func_override_add_guarded("vib.mode", 0x8003FE54u, set_mode, mode_guard, 4, FO_CREDIT_SELF);
} } registration;
}
