"""
src/engines/ffmpeg_adapter.py — FFmpeg Video & Audio Processing Adapter.

Provides utility operations: audio-video muxing, waveform extraction,
transient analysis, and fast mobile preview optimization.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List


class FFmpegAdapter:
    """Helper for media probing, audio-video muxing, and preview transcoding."""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        if ffmpeg_path:
            self.ffmpeg_path = Path(ffmpeg_path)
        else:
            # Check Tesseract bundled bin or system PATH
            bundled_ffmpeg = (
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "Tesseract"
                / "public-cli"
                / "0.1.0-x86_64"
                / "bin"
                / "ffmpeg.exe"
            )
            if bundled_ffmpeg.exists():
                self.ffmpeg_path = bundled_ffmpeg
            else:
                found = shutil.which("ffmpeg")
                self.ffmpeg_path = Path(found) if found else Path("ffmpeg")

    def is_available(self) -> bool:
        try:
            res = subprocess.run(
                [str(self.ffmpeg_path), "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.returncode == 0
        except Exception:
            return False

    def mux_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        shortest: bool = True,
    ) -> bool:
        """Combine video stream and audio stream into a single MP4."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.ffmpeg_path),
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
        ]
        if shortest:
            cmd.append("-shortest")
        cmd.append(str(out))

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return res.returncode == 0 and out.exists()
        except Exception:
            return False

    def create_mobile_preview(
        self,
        input_path: str,
        output_path: str,
        max_height: int = 720,
        crf: int = 26,
    ) -> bool:
        """Transcode to lightweight H.264/AAC for fast Telegram mobile review."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        vf = f"scale=-2:{max_height}"
        cmd = [
            str(self.ffmpeg_path),
            "-y",
            "-i",
            str(input_path),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            str(crf),
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(out),
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return res.returncode == 0 and out.exists()
        except Exception:
            return False
