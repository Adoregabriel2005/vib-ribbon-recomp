#include "iso_reader.h"
#include <array>
#include <iostream>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    PS1::ISOReader disc;
    if (!disc.Open(argv[1])) { std::cerr << "open failed\n"; return 1; }
    std::array<uint8_t, 2352> sector{};
    if (!disc.TrackCount() || !disc.GetSectorCount() || !disc.ReadRawSector(0, sector.data())) return 3;
    std::cout << "tracks=" << disc.TrackCount() << " sectors=" << disc.GetSectorCount()
              << " audio1=" << disc.TrackIsAudio(1) << '\n';
    return 0;
}
