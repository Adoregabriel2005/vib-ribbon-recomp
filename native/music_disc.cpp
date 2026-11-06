#include "music_disc.h"
#include <SDL3/SDL_audio.h>
#include <array>
#include <chrono>
#include <fstream>
#include <memory>
#include <stdexcept>
#define MINIMP3_IMPLEMENTATION
#include "third_party/minimp3/minimp3_ex.h"

namespace vib {
MusicDisc prepare_mp3(const std::filesystem::path& source,
                      const std::filesystem::path& cache) {
    const auto size = std::filesystem::file_size(source);
    if (!size || size > 200ull * 1024 * 1024)
        throw std::runtime_error("O MP3 está vazio ou excede 200 MB.");
    auto decoder = std::make_unique<mp3dec_ex_t>();
    // Map the input instead of retaining a second copy of the entire MP3.
    // The wide API preserves Unicode paths on Windows.
#ifdef _WIN32
    const int opened = mp3dec_ex_open_w(decoder.get(), source.c_str(), MP3D_SEEK_TO_SAMPLE);
#else
    const int opened = mp3dec_ex_open(decoder.get(), source.c_str(), MP3D_SEEK_TO_SAMPLE);
#endif
    if (opened)
        throw std::runtime_error("O arquivo não contém um MP3 válido.");
    struct CloseDecoder { mp3dec_ex_t* p; ~CloseDecoder() { mp3dec_ex_close(p); } } close{decoder.get()};
    if ((decoder->info.channels != 1 && decoder->info.channels != 2) || decoder->info.hz <= 0)
        throw std::runtime_error("Formato de áudio MP3 inválido.");
    SDL_AudioSpec src{SDL_AUDIO_S16, decoder->info.channels, decoder->info.hz};
    SDL_AudioSpec dst{SDL_AUDIO_S16LE, 2, 44100};
    std::unique_ptr<SDL_AudioStream, decltype(&SDL_DestroyAudioStream)> stream(
        SDL_CreateAudioStream(&src, &dst), SDL_DestroyAudioStream);
    if (!stream) throw std::runtime_error("Não foi possível converter o áudio.");

    std::filesystem::create_directories(cache);
    const auto token = std::chrono::steady_clock::now().time_since_epoch().count();
    auto folder = cache / ("track-" + std::to_string(token));
    if (!std::filesystem::create_directory(folder))
        throw std::runtime_error("Não foi possível criar o cache da música.");
    auto part = folder / "audio.part";
    auto bin = folder / "audio.bin";
    auto cue = folder / "audio.cue";
    try {
        std::ofstream output(part, std::ios::binary);
        if (!output) throw std::runtime_error("Não foi possível gravar o cache.");
        uint64_t bytes = 0;
        std::array<char, 16384> converted{};
        auto drain = [&]() {
            for (;;) {
                int count = SDL_GetAudioStreamAvailable(stream.get());
                if (count < 0) throw std::runtime_error("Falha na conversão do áudio.");
                if (!count) break;
                count = SDL_GetAudioStreamData(stream.get(), converted.data(),
                    count < static_cast<int>(converted.size()) ? count : static_cast<int>(converted.size()));
                if (count <= 0) throw std::runtime_error("Falha ao obter o áudio convertido.");
                bytes += static_cast<uint64_t>(count);
                if (bytes > 80ull * 60 * 44100 * 4)
                    throw std::runtime_error("A música excede os 80 minutos de um CD de áudio.");
                output.write(converted.data(), count);
                if (!output) throw std::runtime_error("Espaço insuficiente para preparar a música.");
            }
        };
        std::array<mp3d_sample_t, 8192> samples{};
        for (;;) {
            const size_t count = mp3dec_ex_read(decoder.get(), samples.data(), samples.size());
            if (!count) break;
            if (!SDL_PutAudioStreamData(stream.get(), samples.data(), static_cast<int>(count * sizeof(samples[0]))))
                throw std::runtime_error("Falha ao converter o MP3.");
            drain();
        }
        if (decoder->last_error || !SDL_FlushAudioStream(stream.get()))
            throw std::runtime_error("O MP3 está corrompido ou muda de formato durante a faixa.");
        drain();
        if (!bytes || bytes % 4) throw std::runtime_error("O MP3 não produziu áudio válido.");
        const uint64_t frames = bytes / 4;
        // A CD-DA sector holds exactly 588 stereo frames. Pad only its final tail.
        const size_t padding = static_cast<size_t>((2352 - bytes % 2352) % 2352);
        std::array<char, 2352> silence{};
        output.write(silence.data(), padding);
        output.close();
        if (!output) throw std::runtime_error("Falha ao concluir o cache da música.");
        std::filesystem::rename(part, bin);
        std::ofstream sheet(cue, std::ios::binary);
        sheet << "FILE \"audio.bin\" BINARY\n  TRACK 01 AUDIO\n    INDEX 01 00:00:00\n";
        sheet.close();
        if (!sheet) throw std::runtime_error("Falha ao criar o CD de áudio virtual.");
        return {cue, source.stem().u8string(), frames};
    } catch (...) {
        // These are only the three files created by this conversion, never the source.
        std::error_code ignored;
        std::filesystem::remove(part, ignored);
        std::filesystem::remove(bin, ignored);
        std::filesystem::remove(cue, ignored);
        std::filesystem::remove(folder, ignored);
        throw;
    }
}
}
