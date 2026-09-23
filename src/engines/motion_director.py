"""
src/engines/motion_director.py — Cinematic Motion Graphics & Audio Visualizer Director.

Transforms static music release artwork into high-production kinetic videos:
- Dynamic Ken Burns camera movements (zoom in, pan down, zoom out, pan right, punch-in)
- Real-time audio-reactive neon waveform visualizers
- Cyberpunk brutalist HUD overlays (catalog headers, track chapter cards, telemetry reticles)
- Seamless multi-track montage concatenation for album teasers
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont

from src.catalog.query import MusicCatalogQuery, ReleaseItem, TrackItem


class MotionDirector:
    """Automated Motion Graphics & Audio Visualizer Engine."""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        if ffmpeg_path:
            self.ffmpeg_path = Path(ffmpeg_path)
        else:
            bundled = (
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "Tesseract"
                / "public-cli"
                / "0.1.0-x86_64"
                / "bin"
                / "ffmpeg.exe"
            )
            if bundled.exists():
                self.ffmpeg_path = bundled
            else:
                found = shutil.which("ffmpeg")
                self.ffmpeg_path = Path(found) if found else Path("ffmpeg")

        self.catalog = MusicCatalogQuery()

        # Load fonts
        try:
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf", 52)
            self.font_subtitle = ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf", 32)
            self.font_mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 24)
            self.font_mono_small = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_subtitle = self.font_title
            self.font_mono = self.font_title
            self.font_mono_small = self.font_title

    def create_hud_overlay(
        self,
        output_png: str,
        width: int,
        height: int,
        album_title: str,
        track_number: int,
        total_tracks: int,
        track_title: str,
        metadata_line: str,
        catalog_code: str = "VØID-019",
    ) -> str:
        """Render a cyberpunk / brutalist HUD graphic overlay with transparent background."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cyan = (0, 240, 255)
        cyan_dim = (0, 240, 255, 180)
        white = (255, 255, 255)
        text_dim = (180, 200, 220)
        dark_box = (10, 12, 18, 220)

        # ── Top Header HUD ──
        header_y1 = 60
        header_y2 = 135
        draw.rectangle([40, header_y1, width - 40, header_y2], fill=dark_box, outline=cyan_dim, width=2)
        draw.text((60, header_y1 + 12), f"// VØIDRIDE RECORDS // {catalog_code}", fill=cyan, font=self.font_mono)
        draw.text((60, header_y1 + 38), f"{album_title.upper()} — OFFICIAL ALBUM TEASER", fill=white, font=self.font_subtitle)

        # ── Lower Third Track Badge ──
        badge_y1 = height - 340
        badge_y2 = height - 160
        draw.rectangle([40, badge_y1, width - 40, badge_y2], fill=dark_box, outline=cyan_dim, width=2)

        # Accent tab
        draw.rectangle([40, badge_y1, 48, badge_y2], fill=cyan)

        draw.text((65, badge_y1 + 15), f"TRACK {track_number:02d} // {total_tracks:02d}", fill=cyan, font=self.font_mono)
        draw.text((65, badge_y1 + 45), track_title.upper(), fill=white, font=self.font_title)
        draw.text((65, badge_y1 + 115), metadata_line.upper(), fill=text_dim, font=self.font_mono_small)

        # ── Corner Framing Reticles ──
        b_len = 50
        # Top-Left
        draw.line([(30, 50), (30 + b_len, 50)], fill=cyan, width=3)
        draw.line([(30, 50), (30, 50 + b_len)], fill=cyan, width=3)
        # Top-Right
        draw.line([(width - 30, 50), (width - 30 - b_len, 50)], fill=cyan, width=3)
        draw.line([(width - 30, 50), (width - 30, 50 + b_len)], fill=cyan, width=3)
        # Bottom-Left
        draw.line([(30, height - 50), (30 + b_len, height - 50)], fill=cyan, width=3)
        draw.line([(30, height - 50), (30, height - 50 - b_len)], fill=cyan, width=3)
        # Bottom-Right
        draw.line([(width - 30, height - 50), (width - 30 - b_len, height - 50)], fill=cyan, width=3)
        draw.line([(width - 30, height - 50), (width - 30, height - 50 - b_len)], fill=cyan, width=3)

        out_path = Path(output_png)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return str(out_path)

    def find_track_artwork(self, release_dir: Path, track_name: str) -> Optional[Path]:
        """Find the track-specific cover art or fallback to release cover."""
        covers_dir = release_dir / "covers"
        clean = (
            track_name.lower()
            .replace("0", "")
            .replace("1", "")
            .replace("2", "")
            .replace("3", "")
            .replace("4", "")
            .replace("5", "")
            .replace("_master", "")
            .replace("master", "")
            .strip("_ ")
        )
        if covers_dir.exists():
            for f in covers_dir.glob("*_cover.jpg"):
                if clean in f.name.lower() or f.name.lower().replace("_cover.jpg", "") in clean:
                    return f
            for f in covers_dir.glob("*.jpg"):
                if clean in f.name.lower():
                    return f

        # Fallback to album cover
        for cand in ["album_cover.png", "cover.png", "cover.jpg", "ABYSS_THROTTLE_cover.jpg"]:
            if (release_dir / cand).exists():
                return release_dir / cand
        artwork_albums = Path(r"D:\music\artwork\albums") / release_dir.name
        if artwork_albums.exists():
            for cand in ["album_cover.png", "cover.png", "cover.jpg"]:
                if (artwork_albums / cand).exists():
                    return artwork_albums / cand
        return None

    def render_motion_clip(
        self,
        image_path: str,
        audio_path: str,
        hud_png_path: str,
        output_clip_path: str,
        duration: float = 6.0,
        audio_start: float = 15.0,
        width: int = 1080,
        height: int = 1920,
        motion_type: str = "zoom_in",
    ) -> bool:
        """
        Render a single motion clip with dynamic camera movement,
        audio-reactive neon waveform visualizer, and HUD overlay.
        """
        out = Path(output_clip_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        frames = int(duration * 30)

        # Dynamic motion formulas for zoompan
        if motion_type == "zoom_in":
            motion_filter = f"zoompan=z='min(zoom+0.0012,1.22)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps=30"
        elif motion_type == "pan_down":
            motion_filter = f"zoompan=z=1.15:d={frames}:x='iw/2-(iw/zoom/2)':y='ih*0.05+on*(ih*0.05)/{frames}':s={width}x{height}:fps=30"
        elif motion_type == "zoom_out":
            motion_filter = f"zoompan=z='if(lte(on,-1),1.22,max(1.001,1.22-on*0.0012))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps=30"
        elif motion_type == "pan_right":
            motion_filter = f"zoompan=z=1.15:d={frames}:x='iw*0.05+on*(iw*0.05)/{frames}':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps=30"
        else:  # punch-in climax
            motion_filter = f"zoompan=z='min(zoom+0.0018,1.28)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps=30"

        # Waveform placement: right above the lower badge (y=height-470)
        wave_w = width - 80
        wave_h = 240
        wave_y = height - 480

        filter_str = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{motion_filter}[bg];"
            f"[1:a]showwaves=s={wave_w}x{wave_h}:mode=cline:colors=0x00f0ff:scale=cbrt,colorkey=0x000000:0.1:0.1[waves];"
            f"[bg][waves]overlay=40:{wave_y}[bg_waves];"
            f"[bg_waves][2:v]overlay=0:0[v]"
        )

        cmd = [
            str(self.ffmpeg_path),
            "-y",
            "-loop", "1", "-i", str(image_path),
            "-ss", f"{audio_start:.3f}", "-i", str(audio_path),
            "-loop", "1", "-i", str(hud_png_path),
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "1:a",
            "-t", f"{duration:.3f}",
            "-c:v", "h264_mf", "-b:v", "5M",
            "-c:a", "aac", "-b:a", "256k",
            str(out),
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and out.exists()
        except Exception:
            return False

    def render_album_teaser(
        self,
        slug: str,
        aspect_ratio: str = "9:16",
        total_duration: float = 30.0,
        output_path: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Build and render a full multi-track kinetic montage album teaser:
        - Cycles through 5 master tracks with their distinct individual cover art
        - Alternates 5 camera motions (zoom-in, pan-down, zoom-out, pan-right, climax push-in)
        - Synchronizes audio hooks and real-time audio-reactive neon waveforms
        - Seamlessly concatenates into a single 30.0-second video master
        """
        album = self.catalog.get_release(slug)
        if not album:
            return None

        release_dir = Path(album.release_dir)
        w = 1080 if aspect_ratio == "9:16" else (1920 if aspect_ratio == "16:9" else 1080)
        h = 1920 if aspect_ratio == "9:16" else (1080 if aspect_ratio == "16:9" else 1080)

        # Select top numbered master tracks
        numbered_tracks = [t for t in album.tracks if t.title.startswith(("01", "02", "03", "04", "05"))]
        if not numbered_tracks:
            numbered_tracks = album.tracks[:5]

        count = len(numbered_tracks)
        if count == 0:
            return None

        clip_duration = total_duration / count
        motion_types = ["zoom_in", "pan_down", "zoom_out", "pan_right", "climax"]

        temp_dir = Path(tempfile.mkdtemp(prefix=f"teaser_{slug}_"))
        segment_files = []

        subtitles = [
            "140 BPM // D# MINOR // SUB-BASS TRANSIENT LOCK",
            "144 BPM // HADAL HIGH-PRESSURE SYNTH WALL",
            "140 BPM // ACOUSTIC SIGNATURE DETECTED",
            "142 BPM // SUBMERSIBLE SENSOR LOCK",
            "145 BPM // STRUCTURAL CRUSH // OUT NOW ON VØIDRIDE",
        ]

        try:
            for idx, track in enumerate(numbered_tracks, 1):
                clean_title = track.title.replace("_MASTER", "").replace("MASTER", "")
                if clean_title.startswith(f"0{idx}_"):
                    clean_title = clean_title[3:]

                # 1. Resolve individual track artwork
                art = self.find_track_artwork(release_dir, track.title)
                if not art or not art.exists():
                    art = Path(album.cover_art_path) if album.cover_art_path else None

                if not art or not art.exists():
                    continue

                # 2. Generate custom HUD overlay
                hud_png = temp_dir / f"hud_{idx}.png"
                meta_line = subtitles[(idx - 1) % len(subtitles)]
                self.create_hud_overlay(
                    output_png=str(hud_png),
                    width=w,
                    height=h,
                    album_title=album.title,
                    track_number=idx,
                    total_tracks=count,
                    track_title=clean_title,
                    metadata_line=meta_line,
                    catalog_code="VØID-019",
                )

                # 3. Render 6.0s kinetic motion clip with reactive waveform
                clip_out = temp_dir / f"clip_{idx}.mp4"
                motion = motion_types[(idx - 1) % len(motion_types)]
                audio_start = 15.0  # drop hook start point

                success = self.render_motion_clip(
                    image_path=str(art),
                    audio_path=track.audio_path,
                    hud_png_path=str(hud_png),
                    output_clip_path=str(clip_out),
                    duration=clip_duration,
                    audio_start=audio_start,
                    width=w,
                    height=h,
                    motion_type=motion,
                )

                if success and clip_out.exists():
                    segment_files.append(clip_out)

            if not segment_files:
                return None

            # 4. Concatenate segments with FFmpeg concat demuxer
            concat_list = temp_dir / "concat.txt"
            with open(concat_list, "w", encoding="utf-8") as f:
                for seg in segment_files:
                    f.write(f"file '{seg.resolve()}'\n")

            if not output_path:
                output_dir = Path("D:/hermes-video/output") / slug
                output_dir.mkdir(parents=True, exist_ok=True)
                ratio_code = aspect_ratio.replace(":", "_")
                final_output = output_dir / f"{slug}_album_teaser_{ratio_code}_final.mp4"
            else:
                final_output = Path(output_path)
                final_output.parent.mkdir(parents=True, exist_ok=True)

            cmd_concat = [
                str(self.ffmpeg_path),
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(final_output),
            ]

            res_concat = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=60)
            if res_concat.returncode == 0 and final_output.exists():
                return final_output

        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

        return None

    def render_track_visualizer(
        self,
        slug: str,
        track_number: int,
        aspect_ratio: str = "9:16",
        duration: float = 15.0,
        output_path: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Build and render a motion visualizer for an individual track:
        - Resolves track artwork with dynamic camera motion
        - Cyberpunk HUD metadata badge
        - Real-time reactive neon audio waveform
        """
        album = self.catalog.get_release(slug)
        if not album or not album.tracks:
            return None

        # Find matching track
        track = None
        for t in album.tracks:
            if t.track_number == track_number:
                track = t
                break
        if not track:
            track = album.tracks[0]

        release_dir = Path(album.release_dir)
        w = 1080 if aspect_ratio == "9:16" else (1920 if aspect_ratio == "16:9" else 1080)
        h = 1920 if aspect_ratio == "9:16" else (1080 if aspect_ratio == "16:9" else 1080)

        art = self.find_track_artwork(release_dir, track.title)
        if not art or not art.exists():
            art = Path(album.cover_art_path) if album.cover_art_path else None
        if not art or not art.exists():
            return None

        clean_title = track.title.replace("_MASTER", "").replace("MASTER", "")
        if clean_title.startswith(f"0{track.track_number}_"):
            clean_title = clean_title[3:]

        if not output_path:
            output_dir = Path("D:/hermes-video/output") / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            ratio_code = aspect_ratio.replace(":", "_")
            final_output = output_dir / f"{slug}_t{track.track_number}_{ratio_code}_final.mp4"
        else:
            final_output = Path(output_path)
            final_output.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = Path(tempfile.mkdtemp(prefix=f"vis_{slug}_"))
        try:
            hud_png = temp_dir / "hud.png"
            meta_line = f"{track.bpm or 140} BPM // {track.key or 'D# MINOR'} // SUB-BASS TRANSIENT LOCK"
            self.create_hud_overlay(
                output_png=str(hud_png),
                width=w,
                height=h,
                album_title=album.title,
                track_number=track.track_number,
                total_tracks=album.track_count,
                track_title=clean_title,
                metadata_line=meta_line,
                catalog_code="VØID-019",
            )

            success = self.render_motion_clip(
                image_path=str(art),
                audio_path=track.audio_path,
                hud_png_path=str(hud_png),
                output_clip_path=str(final_output),
                duration=duration,
                audio_start=15.0,
                width=w,
                height=h,
                motion_type="zoom_in",
            )
            if success and final_output.exists():
                return final_output
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        return None
