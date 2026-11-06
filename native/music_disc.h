#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
namespace vib {
struct MusicDisc {
    std::filesystem::path cue;
    std::string title;
    uint64_t frames = 0;
    double seconds() const { return static_cast<double>(frames) / 44100.0; }
};
// Offline conversion only. Playback remains the guest's CD-ROM/CDDA/SPU path.
MusicDisc prepare_mp3(const std::filesystem::path& source,
                      const std::filesystem::path& cache);
}
