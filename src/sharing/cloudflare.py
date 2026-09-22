"""
src/sharing/cloudflare.py — Cloudflare Tunnel & Secure-Share Bridge.

Packages video renders and deliverables, exposes them over an ephemeral
Cloudflare Tunnel (trycloudflare.com), and extracts the external review link.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ShareResult:
    success: bool
    local_url: Optional[str] = None
    external_url: Optional[str] = None
    packaged_path: Optional[str] = None
    error: Optional[str] = None


class CloudflareShare:
    """Wrapper for the secure-share Cloudflare tunnel pipeline."""

    def __init__(self, script_path: Optional[str] = None):
        if script_path:
            self.script_path = Path(script_path)
        else:
            env_script = os.environ.get("SECURE_SHARE_SCRIPT")
            if env_script:
                self.script_path = Path(env_script)
            else:
                self.script_path = (
                    Path(r"C:\Users\maxin\.gemini\antigravity\skills\secure-share\scripts\share.py")
                )

    def is_available(self) -> bool:
        return self.script_path.exists()

    def package_and_share(self, target_path: str) -> ShareResult:
        """
        Execute share.py on a video file or project directory.
        Parses [LOCAL LINK] and [EXTERNAL LINK] from stdout.
        """
        target = Path(target_path)
        if not target.exists():
            return ShareResult(
                success=False,
                error=f"Target file or directory does not exist: {target_path}",
            )

        if not self.script_path.exists():
            return ShareResult(
                success=False,
                error=f"secure-share script not found at: {self.script_path}",
            )

        cmd = [sys.executable, str(self.script_path), "--path", str(target)]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            stdout = res.stdout
            local_url = None
            external_url = None
            packaged_path = None

            # Parse [LOCAL LINK]
            local_match = re.search(r"\[LOCAL LINK\]\s+(https?://\S+)", stdout)
            if local_match:
                local_url = local_match.group(1).strip()

            # Parse [EXTERNAL LINK]
            ext_match = re.search(r"\[EXTERNAL LINK\]\s+(https?://\S+)", stdout)
            if ext_match:
                external_url = ext_match.group(1).strip()

            # Parse [SUCCESS] Packaged successfully: <path>
            pkg_match = re.search(r"\[SUCCESS\] Packaged successfully:\s+(.+)", stdout)
            if pkg_match:
                packaged_path = pkg_match.group(1).strip()

            return ShareResult(
                success=True if (external_url or local_url) else False,
                local_url=local_url,
                external_url=external_url,
                packaged_path=packaged_path,
                error=res.stderr.strip() if res.returncode != 0 else None,
            )

        except Exception as e:
            return ShareResult(
                success=False,
                error=f"Exception executing secure-share: {e}",
            )
