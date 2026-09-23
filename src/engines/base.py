"""
src/engines/base.py — Abstract Video Engine Interface.

Allows hermes-video to interact with local engines (Tesseract by Mirage)
and seamlessly wire future cloud or AI services (Runway, ComfyUI, Luma, Kling, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class VideoProjectSpec:
    name: str
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: float = 15.0
    aspect_ratio: str = "16:9"
    audio_track_path: Optional[str] = None
    cover_art_path: Optional[str] = None
    assets: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    success: bool
    output_path: Optional[str] = None
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseVideoEngine(ABC):
    """Abstract base class for all video synthesis and rendering engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the engine provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if local binary or remote API is configured and operational."""
        pass

    @abstractmethod
    def create_project(self, spec: VideoProjectSpec, project_path: str) -> EngineResult:
        """Create and initialize a new project document or session."""
        pass

    @abstractmethod
    def render_preview(
        self, project_path: str, timestamp_seconds: float, output_image_path: str
    ) -> EngineResult:
        """Render a single frame snapshot at a specific timestamp."""
        pass

    @abstractmethod
    def render_filmstrip(
        self, project_path: str, output_image_path: str, frames: int = 9
    ) -> EngineResult:
        """Render a visual filmstrip grid for review."""
        pass

    @abstractmethod
    def export(
        self, project_path: str, output_video_path: str, preset: str = "mp4"
    ) -> EngineResult:
        """Render the complete video package to disk."""
        pass
