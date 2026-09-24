"""
src/templates/manager.py — Production Brief & Style Template Manager.

Persists and manages video production templates for hermes-video:
- Built-in studio presets (Cyberpunk Deep Sea, Industrial Acid, Crimson Breach, Monochrome Void)
- User-saved custom templates with persistent JSON storage
- One-tap template retrieval and application to any release or track
"""

import os
import json
import uuid
import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any


@dataclass
class ProductionBrief:
    id: str
    name: str
    theme: str
    color_palette: str  # "cyan_purple", "acid_green", "crimson_red", "monochrome_gold"
    primary_color: str  # Hex string (e.g. "#00f0ff")
    accent_color: str   # Hex string (e.g. "#7000ff")
    camera_motion: str  # "push_in", "pan_drift", "punch_climax", "ambient_float"
    typography_style: str  # "brutalist_mono", "warning_industrial", "minimal_clean"
    waveform_style: str  # "cyan", "green", "red", "gold", "white"
    waveform_hex: str = "0x00f0ff"
    subtitles: List[str] = field(default_factory=list)
    raw_prompt: Optional[str] = None
    created_at: Optional[str] = None
    is_built_in: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionBrief":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


BUILTIN_TEMPLATES: List[ProductionBrief] = [
    ProductionBrief(
        id="tpl_cyberpunk_sea",
        name="Cyberpunk Deep Sea",
        theme="Bioluminescent abyssal trenches, deep crushing pressure, high-contrast cyan lighting",
        color_palette="cyan_purple",
        primary_color="#00f0ff",
        accent_color="#7000ff",
        camera_motion="push_in",
        typography_style="brutalist_mono",
        waveform_style="cyan",
        waveform_hex="0x00f0ff",
        subtitles=[
            "140 BPM // D# MINOR // SUB-BASS TRANSIENT LOCK",
            "144 BPM // HADAL HIGH-PRESSURE SYNTH WALL",
            "140 BPM // ACOUSTIC SIGNATURE DETECTED",
            "142 BPM // SUBMERSIBLE SENSOR LOCK",
            "145 BPM // STRUCTURAL CRUSH // OUT NOW ON VØIDRIDE",
        ],
        raw_prompt="Deep sea underwater trench with neon cyan submersibles and heavy sub-bass pulsing",
        created_at="2026-01-01T00:00:00Z",
        is_built_in=True,
    ),
    ProductionBrief(
        id="tpl_industrial_acid",
        name="Industrial Acid",
        theme="Corrosive chemical facilities, toxic biohazard warning palettes, high-speed lateral motion",
        color_palette="acid_green",
        primary_color="#39ff14",
        accent_color="#00ffcc",
        camera_motion="pan_drift",
        typography_style="warning_industrial",
        waveform_style="green",
        waveform_hex="0x39ff14",
        subtitles=[
            "150 BPM // F MINOR // TOXIC CONTAINMENT BREACH",
            "150 BPM // CAUSTIC ACID FILTER SWEEP",
            "152 BPM // REACTOR RUNAWAY TELEMETRY",
            "148 BPM // EMERGENCY VENT SEQUENCE",
            "155 BPM // SYSTEM PURGE // OUT NOW ON VØIDRIDE",
        ],
        raw_prompt="Acid green industrial biohazard factory with toxic lighting and fast pacing",
        created_at="2026-01-01T00:00:00Z",
        is_built_in=True,
    ),
    ProductionBrief(
        id="tpl_crimson_breach",
        name="Crimson Breach",
        theme="Catastrophic hull failure, red emergency strobes, aggressive kinetic zoom punches",
        color_palette="crimson_red",
        primary_color="#ff003c",
        accent_color="#ff8800",
        camera_motion="punch_climax",
        typography_style="brutalist_mono",
        waveform_style="red",
        waveform_hex="0xff003c",
        subtitles=[
            "145 BPM // C# MINOR // CRITICAL HULL INTEGRITY",
            "145 BPM // EMERGENCY KINETIC OVERLOAD",
            "148 BPM // BULKHEAD STRUCTURAL FAULT",
            "142 BPM // EVACUATION CORRIDOR COMPROMISED",
            "150 BPM // FINAL IMPACT // OUT NOW ON VØIDRIDE",
        ],
        raw_prompt="Blood red emergency alarm lighting, explosive bass hits and aggressive camera shakes",
        created_at="2026-01-01T00:00:00Z",
        is_built_in=True,
    ),
    ProductionBrief(
        id="tpl_monochrome_void",
        name="Monochrome Void",
        theme="Obsidian black minimalism, sharp stark white telemetry typography, slow floating camera",
        color_palette="monochrome_gold",
        primary_color="#ffffff",
        accent_color="#ffb000",
        camera_motion="ambient_float",
        typography_style="minimal_clean",
        waveform_style="gold",
        waveform_hex="0xffb000",
        subtitles=[
            "138 BPM // A MINOR // OBSIDIAN HORIZON SCAN",
            "138 BPM // ZERO-GRAVITY SUB-HARMONICS",
            "140 BPM // MONOCHROME PHASE COHERENCE",
            "136 BPM // VACUUM PRESSURE INERTIA",
            "142 BPM // ABSOLUTE ZERO // OUT NOW ON VØIDRIDE",
        ],
        raw_prompt="Stark monochrome brutalist void with warm golden telemetry and smooth floating motion",
        created_at="2026-01-01T00:00:00Z",
        is_built_in=True,
    ),
]


class TemplateManager:
    """Persistent storage and lifecycle for video style templates."""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            root = Path(__file__).resolve().parent.parent.parent
            self.storage_path = root / "data" / "templates.json"

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage()

    def _ensure_storage(self):
        """Initialize templates file with built-in templates if not present."""
        if not self.storage_path.exists():
            data = {"templates": [t.to_dict() for t in BUILTIN_TEMPLATES]}
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def list_templates(self) -> List[ProductionBrief]:
        """List all available templates (built-in and custom user-saved)."""
        self._ensure_storage()
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            templates = [ProductionBrief.from_dict(t) for t in data.get("templates", [])]
            return templates
        except Exception:
            return BUILTIN_TEMPLATES

    def get_template(self, template_id: str) -> Optional[ProductionBrief]:
        """Get template by ID."""
        for t in self.list_templates():
            if t.id == template_id:
                return t
        return None

    def save_template(
        self,
        brief: ProductionBrief,
        name: Optional[str] = None,
    ) -> ProductionBrief:
        """Save a new custom template or update existing."""
        templates = self.list_templates()
        new_id = brief.id if (brief.id and brief.id.startswith("custom_")) else f"custom_{uuid.uuid4().hex[:8]}"
        custom_name = name or brief.name or "Custom Production Style"

        new_brief = ProductionBrief(
            id=new_id,
            name=custom_name,
            theme=brief.theme,
            color_palette=brief.color_palette,
            primary_color=brief.primary_color,
            accent_color=brief.accent_color,
            camera_motion=brief.camera_motion,
            typography_style=brief.typography_style,
            waveform_style=brief.waveform_style,
            waveform_hex=brief.waveform_hex,
            subtitles=list(brief.subtitles),
            raw_prompt=brief.raw_prompt,
            created_at=datetime.datetime.utcnow().isoformat() + "Z",
            is_built_in=False,
        )

        # Replace or append
        existing_idx = next((i for i, t in enumerate(templates) if t.id == new_id), None)
        if existing_idx is not None:
            templates[existing_idx] = new_brief
        else:
            templates.append(new_brief)

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({"templates": [t.to_dict() for t in templates]}, f, indent=2)

        return new_brief

    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template (built-ins cannot be deleted)."""
        templates = self.list_templates()
        target = next((t for t in templates if t.id == template_id), None)
        if not target or target.is_built_in:
            return False

        updated = [t for t in templates if t.id != template_id]
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({"templates": [t.to_dict() for t in updated]}, f, indent=2)
        return True
