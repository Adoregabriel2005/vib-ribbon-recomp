#include "music_disc.h"
#include <iostream>
int main(int argc, char** argv) {
    if (argc != 3) { std::cerr << "usage: vib-music-tool MP3 CACHE\n"; return 2; }
    try {
        auto disc = vib::prepare_mp3(std::filesystem::u8path(argv[1]), std::filesystem::u8path(argv[2]));
        std::cout << disc.cue.u8string() << '\n' << disc.frames << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
