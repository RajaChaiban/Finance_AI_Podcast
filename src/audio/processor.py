import os
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from src.utils.logger import log


class AudioProcessor:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_mp3(self, audio: np.ndarray, sample_rate: int, date: str, podcast_name: str = "Market Pulse") -> str:
        filename = f"{date}-{podcast_name.lower().replace(' ', '-')}.mp3"
        mp3_path = os.path.join(self.output_dir, filename)

        # Save as WAV first (soundfile doesn't write MP3 directly)
        wav_path = mp3_path.replace(".mp3", ".wav")
        sf.write(wav_path, audio, sample_rate)
        log.info(f"WAV written: {wav_path}")

        # Convert to MP3 via pydub
        audio_segment = AudioSegment.from_wav(wav_path)

        # Normalize audio levels
        audio_segment = self.normalize(audio_segment)

        audio_segment.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": f"{podcast_name} -- {date}",
                "artist": podcast_name,
                "album": podcast_name,
                "genre": "Podcast",
            },
        )

        # Clean up WAV
        os.remove(wav_path)
        file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
        log.info(f"MP3 saved: {mp3_path} ({file_size_mb:.1f} MB)")
        return mp3_path

    def normalize(self, audio: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
        change = target_dbfs - audio.dBFS
        return audio.apply_gain(change)
