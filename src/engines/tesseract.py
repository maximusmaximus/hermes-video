"""
src/engines/tesseract.py — Tesseract by Mirage Engine Adapter.

Executes local video editing, native motion graphics, and filmstrip/export
rendering via the verified Mirage Tesseract CLI.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base import BaseVideoEngine, VideoProjectSpec, EngineResult


class TesseractEngine(BaseVideoEngine):
    """Local GPU-accelerated video synthesis using Tesseract CLI."""

    def __init__(self, cli_path: Optional[str] = None):
        if cli_path:
            self.cli_path = Path(cli_path)
        else:
            # Check environment or default to Windows LocalAppData location
            env_bin = os.environ.get("TESSERACT_BIN")
            if env_bin:
                self.cli_path = Path(env_bin)
            else:
                local_app = os.environ.get("LOCALAPPDATA", "")
                self.cli_path = Path(local_app) / "Tesseract" / "bin" / "tsrct.cmd"

    @property
    def name(self) -> str:
        return "tesseract"

    def is_available(self) -> bool:
        """Check if tsrct executable exists and reports valid version."""
        if not self.cli_path.exists():
            # Check PATH
            found = shutil.which("tsrct")
            if found:
                self.cli_path = Path(found)
            else:
                return False
        try:
            res = subprocess.run(
                [str(self.cli_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return res.returncode == 0 and "tsrct" in res.stdout
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Return the reported version of the Tesseract CLI."""
        try:
            res = subprocess.run(
                [str(self.cli_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def create_project(self, spec: VideoProjectSpec, project_path: str) -> EngineResult:
        """Create a new .tsrct document with customized dimensions, duration, and visual layers."""
        p_path = Path(project_path)
        p_path.parent.mkdir(parents=True, exist_ok=True)
        if p_path.exists():
            try:
                p_path.unlink()
            except Exception:
                pass

        # Step 1: Base project creation
        cmd = [
            str(self.cli_path),
            "project",
            "create",
            "--project",
            str(p_path),
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                return EngineResult(
                    success=False,
                    error=res.stderr.strip() or res.stdout.strip(),
                    message="Failed to create Tesseract project",
                )
        except Exception as e:
            return EngineResult(
                success=False,
                error=str(e),
                message="Exception during project create",
            )

        # Step 2: Import artwork image asset if available
        art_path = None
        if getattr(spec, "cover_art_path", None) and os.path.exists(spec.cover_art_path):
            art_path = Path(spec.cover_art_path)
        elif spec.assets:
            for a in spec.assets:
                if Path(a).suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"] and os.path.exists(a):
                    art_path = Path(a)
                    break

        if not art_path:
            # Fallback 1: check audio track parent directory
            if spec.audio_track_path and os.path.exists(spec.audio_track_path):
                track_dir = Path(spec.audio_track_path).parent
                for cand in ["cover.png", "cover.jpg", "album_cover.png"]:
                    if (track_dir / cand).exists():
                        art_path = track_dir / cand
                        break
            # Fallback 2: check if any album slug matches project path or name
            if not art_path:
                artwork_root = Path(r"D:\music\artwork\albums")
                if artwork_root.exists():
                    search_str = f"{project_path} {spec.name}".lower()
                    for slug_dir in artwork_root.iterdir():
                        if slug_dir.is_dir() and slug_dir.name.lower() in search_str:
                            for cand in ["album_cover.png", "cover.png", "cover.jpg"]:
                                if (slug_dir / cand).exists():
                                    art_path = slug_dir / cand
                                    break
                        if art_path:
                            break

        artwork_imported = False
        if art_path and art_path.exists():
            imp_cmd = [
                str(self.cli_path),
                "project",
                "import-asset",
                "--project",
                str(p_path),
                "--file",
                str(art_path),
                "--asset-id",
                "cover_art",
                "--kind",
                "image",
            ]
            imp_res = subprocess.run(imp_cmd, capture_output=True, text=True, timeout=30)
            if imp_res.returncode == 0:
                artwork_imported = True

        # Step 3: Checkout editable document JSON
        editable_path = p_path.parent / f"{p_path.stem}_editable.json"
        chk_cmd = [
            str(self.cli_path),
            "project",
            "checkout",
            "--project",
            str(p_path),
            "--output",
            str(editable_path),
        ]
        chk_res = subprocess.run(chk_cmd, capture_output=True, text=True, timeout=30)
        if chk_res.returncode != 0 or not editable_path.exists():
            return EngineResult(
                success=True,
                output_path=str(p_path),
                message=f"Created base project: {p_path.name} (checkout skipped)",
                metadata={"spec": spec.name, "duration": spec.duration},
            )

        # Step 4: Configure duration, dimensions, and visual layers
        try:
            with open(editable_path, "r", encoding="utf-8") as f:
                doc = json.load(f)

            duration_sec = float(spec.duration) if spec.duration else 15.0
            doc["duration"] = duration_sec
            doc["dimensions"] = {"width": spec.width, "height": spec.height}

            duration_ms = int(duration_sec * 1000)
            layers = []
            layer_id = 1

            # Top visual layer: High-resolution artwork
            if artwork_imported:
                # Center artwork proportionally
                pos_x = int((spec.width - spec.height) / 2) if spec.width > spec.height else 0
                pos_y = int((spec.height - spec.width) / 2) if spec.height > spec.width else 0
                layers.append({
                    "type": "Image",
                    "id": layer_id,
                    "name": "Album Artwork",
                    "activeRange": {"start": 0, "duration": duration_ms},
                    "transform": {
                        "anchorPoint": [0, 0],
                        "position": [pos_x, pos_y],
                        "scale": [100, 100],
                        "rotation": 0,
                        "opacity": 100,
                    },
                    "source": {
                        "assetId": "cover_art",
                        "fit": "contain",
                    },
                })
                layer_id += 1

            # Background layer: Dark brutalist carbon black
            layers.append({
                "type": "Rect",
                "id": layer_id,
                "name": "Background",
                "activeRange": {"start": 0, "duration": duration_ms},
                "transform": {
                    "anchorPoint": [0, 0],
                    "position": [0, 0],
                    "scale": [100, 100],
                    "rotation": 0,
                    "opacity": 100,
                },
                "rect": {
                    "size": [spec.width, spec.height],
                    "fillColor": [0.03, 0.03, 0.05, 1.0],
                },
            })

            doc["composition"]["layers"] = layers

            with open(editable_path, "w", encoding="utf-8") as f:
                json.dump(doc, f, indent=2)

            # Step 5: Commit customized project document
            cmt_cmd = [
                str(self.cli_path),
                "project",
                "commit",
                "--project",
                str(p_path),
                "--file",
                str(editable_path),
            ]
            cmt_res = subprocess.run(cmt_cmd, capture_output=True, text=True, timeout=30)
            if cmt_res.returncode != 0:
                print(f"[WARN] Tesseract commit error: {cmt_res.stderr.strip()}")

        except Exception as e:
            print(f"[WARN] Failed to customize project layers: {e}")
        finally:
            if editable_path.exists():
                try:
                    editable_path.unlink()
                except Exception:
                    pass

        return EngineResult(
            success=True,
            output_path=str(p_path),
            message=f"Created Tesseract project with visual layers: {p_path.name}",
            metadata={"spec": spec.name, "duration": spec.duration, "artwork": artwork_imported},
        )

    def render_preview(
        self, project_path: str, timestamp_seconds: float, output_image_path: str
    ) -> EngineResult:
        """Render a single frame snapshot at a timestamp."""
        out = Path(output_image_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # tsrct preview --project <PROJECT> --time <TIME> --output <OUTPUT>
        time_str = f"{timestamp_seconds:.3f}"
        cmd = [
            str(self.cli_path),
            "preview",
            "--project",
            str(project_path),
            "--time",
            time_str,
            "--output",
            str(out),
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode != 0:
                return EngineResult(
                    success=False,
                    error=res.stderr.strip() or res.stdout.strip(),
                    message="Failed to render preview frame",
                )

            return EngineResult(
                success=True,
                output_path=str(out),
                message=f"Rendered preview frame at {time_str}",
            )
        except Exception as e:
            return EngineResult(
                success=False,
                error=str(e),
                message="Exception during preview render",
            )

    def render_filmstrip(
        self, project_path: str, output_image_path: str, frames: int = 9
    ) -> EngineResult:
        """Render a filmstrip grid of project frames."""
        out = Path(output_image_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.cli_path),
            "filmstrip",
            "--project",
            str(project_path),
            "--output",
            str(out),
            "--max-frames",
            str(frames),
            "--items-per-row",
            "3" if frames <= 9 else "5",
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if res.returncode != 0:
                return EngineResult(
                    success=False,
                    error=res.stderr.strip() or res.stdout.strip(),
                    message="Failed to render filmstrip",
                )

            return EngineResult(
                success=True,
                output_path=str(out),
                message=f"Rendered {frames}-frame filmstrip",
            )
        except Exception as e:
            return EngineResult(
                success=False,
                error=str(e),
                message="Exception during filmstrip render",
            )

    def export(
        self, project_path: str, output_video_path: str, preset: str = "mp4"
    ) -> EngineResult:
        """Export project to MP4 or ProRes MOV."""
        out = Path(output_video_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.cli_path),
            "export",
            "--project",
            str(project_path),
            "--output",
            str(out),
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode != 0:
                return EngineResult(
                    success=False,
                    error=res.stderr.strip() or res.stdout.strip(),
                    message="Export failed",
                )

            return EngineResult(
                success=True,
                output_path=str(out),
                message=f"Exported video to {out}",
            )
        except Exception as e:
            return EngineResult(
                success=False,
                error=str(e),
                message="Exception during video export",
            )
