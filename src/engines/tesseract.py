"""
src/engines/tesseract.py — Tesseract by Mirage Engine Adapter.

Executes local video editing, native motion graphics, and filmstrip/export
rendering via the verified Mirage Tesseract CLI.
"""

import os
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
        """Create a new .tsrct document using `tsrct project create`."""
        p_path = Path(project_path)
        p_path.parent.mkdir(parents=True, exist_ok=True)

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

            return EngineResult(
                success=True,
                output_path=str(p_path),
                message=f"Created Tesseract project: {p_path.name}",
                metadata={"spec": spec.name, "duration": spec.duration},
            )
        except Exception as e:
            return EngineResult(
                success=False,
                error=str(e),
                message="Exception during project create",
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
