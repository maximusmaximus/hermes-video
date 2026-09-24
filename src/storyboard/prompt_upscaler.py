"""
src/storyboard/prompt_upscaler.py — Venice AI Prompt Upscaler & Creative Director.

Expands raw user concepts into structured 6-Vector Production Briefs:
- Venice Inference (deepseek-v4-flash) under daily Controller budget ($1.00)
- Fallback deterministic heuristic synthesis if offline or budget reached
- Interactive parameter modification (palette, camera motion, typography)
"""

import os
import json
import re
import uuid
import datetime
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from src.budget.ledger import BudgetLedger
from src.templates.manager import ProductionBrief, BUILTIN_TEMPLATES

# Standard palette mappings
COLOR_PALETTES = {
    "cyan_purple": {
        "name": "Cyberpunk Cyan & Neon Violet",
        "primary": "#00f0ff",
        "accent": "#7000ff",
        "waveform_hex": "0x00f0ff",
        "waveform_style": "cyan",
    },
    "acid_green": {
        "name": "Toxic Biohazard Acid Green",
        "primary": "#39ff14",
        "accent": "#00ffcc",
        "waveform_hex": "0x39ff14",
        "waveform_style": "green",
    },
    "crimson_red": {
        "name": "Emergency Breach Crimson Red",
        "primary": "#ff003c",
        "accent": "#ff8800",
        "waveform_hex": "0xff003c",
        "waveform_style": "red",
    },
    "monochrome_gold": {
        "name": "Minimal Obsidian & Amber Gold",
        "primary": "#ffffff",
        "accent": "#ffb000",
        "waveform_hex": "0xffb000",
        "waveform_style": "gold",
    },
}

CAMERA_MOTIONS = {
    "push_in": "Kinetic Z-Axis Push-In (Forward Tension)",
    "pan_drift": "Lateral Horizontal Pan Drift (Atmospheric)",
    "punch_climax": "Aggressive Climax Zoom Punch (Drop Impact)",
    "ambient_float": "Smooth Zero-G Ambient Float (Hypnotic)",
    "zoom_out": "Wide Abyssal Pull-Back (Scale Reveal)",
}

TYPOGRAPHY_STYLES = {
    "brutalist_mono": "Brutalist Monospace Telemetry (Consolas/Bahnschrift)",
    "warning_industrial": "Heavy Industrial Warning Stencil (High Contrast)",
    "minimal_clean": "Clean Obsidian Swiss Sans (Understated)",
}


class PromptUpscaler:
    """Uses Venice AI inference to upscale creative prompts into production briefs."""

    def __init__(
        self,
        budget_ledger: Optional[BudgetLedger] = None,
        api_key: Optional[str] = None,
        api_url: str = "https://api.venice.ai/api/v1/chat/completions",
        model: str = "mistral-small-3-2-24b-instruct",
    ):
        self.budget_ledger = budget_ledger or BudgetLedger()
        self.api_url = api_url
        self.model = model

        # Resolve Venice controller key
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("VENICE_CONTROLLER_KEY")
            if not self.api_key:
                env_path = Path(__file__).resolve().parent.parent.parent / ".env"
                if env_path.exists():
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("VENICE_CONTROLLER_KEY="):
                                self.api_key = line.strip().split("=", 1)[1].strip()
                                break

    def upscale_prompt(
        self,
        raw_prompt: str,
        album_name: str = "Abyss Throttle",
        track_name: Optional[str] = None,
        genre: str = "Industrial Cyberpunk",
    ) -> ProductionBrief:
        """
        Upscale raw user prompt into a structured ProductionBrief.
        Guarded by BudgetLedger; falls back gracefully if budget exceeded or offline.
        """
        raw_prompt = raw_prompt.strip()
        if not raw_prompt:
            # Return default studio template
            base = BUILTIN_TEMPLATES[0]
            return ProductionBrief(
                id=f"brief_{uuid.uuid4().hex[:8]}",
                name=base.name,
                theme=base.theme,
                color_palette=base.color_palette,
                primary_color=base.primary_color,
                accent_color=base.accent_color,
                camera_motion=base.camera_motion,
                typography_style=base.typography_style,
                waveform_style=base.waveform_style,
                waveform_hex=base.waveform_hex,
                subtitles=list(base.subtitles),
                raw_prompt="Studio Default",
                created_at=datetime.datetime.utcnow().isoformat() + "Z",
                is_built_in=False,
            )

        # Check budget authorization
        projected_cost = 0.002
        authorized, reason = self.budget_ledger.check_authorization("controller", projected_cost)

        if authorized and self.api_key:
            brief = self._call_venice_upscale(raw_prompt, album_name, track_name, genre)
            if brief:
                return brief

        # Deterministic heuristic fallback
        return self._heuristic_fallback(raw_prompt, album_name, track_name, genre)

    def _call_venice_upscale(
        self,
        raw_prompt: str,
        album_name: str,
        track_name: Optional[str],
        genre: str,
    ) -> Optional[ProductionBrief]:
        """Query Venice AI for intelligent brief expansion."""
        models_to_try = [self.model]
        if "mistral" in self.model:
            models_to_try.append("deepseek-v4-flash")
        elif "deepseek" in self.model:
            models_to_try.append("mistral-small-3-2-24b-instruct")

        system_prompt = (
            "You are the Chief Motion Graphics & Visual Director for VØIDRIDE Records.\n"
            "Your task: Transform the user's creative prompt into a precise 6-Vector Video Production Brief adhering to the brutalist cyberpunk studio aesthetic.\n\n"
            "OUTPUT RULES:\n"
            "1. Output ONLY a valid JSON object. No explanation, no markdown text outside the JSON.\n"
            "2. Fields required:\n"
            "   - name: Short evocative 2-4 word style name (e.g. 'Abyssal Flare', 'Martian Firestorm', 'Neon Acid Breach')\n"
            "   - theme: 1-2 punchy sentences describing lighting, textures, particle effects, and mood\n"
            "   - color_palette: Exactly one of ['cyan_purple', 'acid_green', 'crimson_red', 'monochrome_gold']\n"
            "   - primary_color: Hex color string (e.g. '#00f0ff', '#39ff14', '#ff003c', '#ff3300', '#ffffff')\n"
            "   - accent_color: Secondary hex color string (e.g. '#7000ff', '#00ffcc', '#ff8800', '#ffb000')\n"
            "   - camera_motion: Exactly one of ['push_in', 'pan_drift', 'punch_climax', 'ambient_float', 'zoom_out']\n"
            "   - typography_style: Exactly one of ['brutalist_mono', 'warning_industrial', 'minimal_clean']\n"
            "   - waveform_style: One of ['cyan', 'green', 'red', 'gold', 'white']\n"
            "   - waveform_hex: 0x followed by 6 hex chars (e.g. '0x00f0ff', '0xff3300')\n"
            "   - subtitles: An array of exactly 5 brutalist telemetry / track overlay captions matching the concept\n"
        )

        user_content = (
            f"User Concept: \"{raw_prompt}\"\n"
            f"Release: \"{album_name}\"\n"
            f"Track: \"{track_name or 'Album Montage'}\"\n"
            f"Musical Genre: \"{genre}\"\n"
        )

        for current_model in models_to_try:
            payload = {
                "model": current_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.3,
                "max_tokens": 800,
            }

            req = urllib.request.Request(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(payload).encode("utf-8"),
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})
                in_tokens = usage.get("prompt_tokens", 800)
                out_tokens = usage.get("completion_tokens", 350)

                # Record in Budget Ledger
                cost = self.budget_ledger.calculate_cost(current_model, in_tokens, out_tokens)
                self.budget_ledger.record_usage(
                    role="controller",
                    model=current_model,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    cost_usd=cost,
                    metadata={"action": "prompt_upscale", "prompt": raw_prompt[:60]},
                )

                # Parse JSON from content (strip markdown tags or whitespace)
                clean = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.MULTILINE)
                clean = re.sub(r"```$", "", clean.strip(), flags=re.MULTILINE)
                match = re.search(r"\{.*\}", clean, re.DOTALL)
                if match:
                    clean = match.group(0)

                parsed = json.loads(clean)

                # Ensure palette consistency
                palette_key = parsed.get("color_palette", "cyan_purple")
                if palette_key not in COLOR_PALETTES:
                    palette_key = "cyan_purple"
                ref_pal = COLOR_PALETTES[palette_key]

                primary = parsed.get("primary_color") or ref_pal["primary"]
                accent = parsed.get("accent_color") or ref_pal["accent"]
                waveform_hex = parsed.get("waveform_hex") or ref_pal["waveform_hex"]

                subs = parsed.get("subtitles", [])
                if not isinstance(subs, list) or len(subs) < 5:
                    subs = [
                        f"140 BPM // {album_name.upper()} // TRANSIENT LOCK",
                        "144 BPM // RESONANT SUB-BASS MODULATION",
                        "140 BPM // TELEMETRY LINK ESTABLISHED",
                        "142 BPM // KINETIC PHASE COHERENCE",
                        f"145 BPM // {album_name.upper()} // OUT NOW ON VØIDRIDE",
                    ]

                return ProductionBrief(
                    id=f"brief_{uuid.uuid4().hex[:8]}",
                    name=parsed.get("name", "Upscaled Style Brief"),
                    theme=parsed.get("theme", f"Cinematic brutalist visualizer tailored for {album_name}"),
                    color_palette=palette_key,
                    primary_color=primary,
                    accent_color=accent,
                    camera_motion=parsed.get("camera_motion", "push_in"),
                    typography_style=parsed.get("typography_style", "brutalist_mono"),
                    waveform_style=parsed.get("waveform_style", ref_pal["waveform_style"]),
                    waveform_hex=waveform_hex,
                    subtitles=subs[:5],
                    raw_prompt=raw_prompt,
                    created_at=datetime.datetime.utcnow().isoformat() + "Z",
                    is_built_in=False,
                )

            except Exception:
                continue

        return None

    def _heuristic_fallback(
        self,
        raw_prompt: str,
        album_name: str,
        track_name: Optional[str],
        genre: str,
    ) -> ProductionBrief:
        """Deterministic smart keyword matcher for offline or budget-limited scenarios."""
        lower = raw_prompt.lower()

        if any(w in lower for w in ["mars", "desert", "burning", "fire", "mad max", "flame", "apocalypse", "inferno", "dune", "wasteland", "pyro"]):
            palette_key = "crimson_red"
            motion = "punch_climax"
            name = "Martian Mad Max Wasteland"
            theme = "Scorched Martian red dunes, burning neon pyres, apocalyptic Mad Max dust storms, and violent atmospheric drop impacts."
            typo = "warning_industrial"
            primary_override = "#ff3300"
            accent_override = "#ff8800"
            waveform_override = "0xff3300"
            subtitles = [
                f"145 BPM // {album_name.upper()} // MARS ATMOSPHERIC ENTRY",
                "145 BPM // APOCALYPTIC DUST FIRES // SECTOR 04",
                "148 BPM // XENOMORPHIC BREACH CONFIRMED",
                "146 BPM // BURNING MAN PYROCLASTIC TRANSIENTS",
                f"150 BPM // {album_name.upper()} // OUT NOW ON VØIDRIDE",
            ]
        elif any(w in lower for w in ["alien", "horror", "monster", "xeno", "xenomorph", "dread", "nightmare", "creature", "terror", "creepy"]):
            palette_key = "acid_green"
            motion = "punch_climax"
            name = "Xenomorphic Horror Protocol"
            theme = "Subterranean xenomorphic bio-horror, flickering emergency stroboscopic lighting, and high-tension dread."
            typo = "warning_industrial"
            primary_override = "#39ff14"
            accent_override = "#9900ff"
            waveform_override = "0x39ff14"
            subtitles = [
                f"140 BPM // {album_name.upper()} // LIFEFORM DETECTED",
                "142 BPM // CONTAINMENT BREACH // SECTOR HAZARD",
                "145 BPM // XENO TRANSIENT ATTACK VECTOR",
                "144 BPM // NEUROTOXIC PULSE COHERENCE",
                f"148 BPM // {album_name.upper()} // OUT NOW ON VØIDRIDE",
            ]
        elif any(w in lower for w in ["acid", "green", "toxic", "biohazard", "corrosive", "chemical"]):
            palette_key = "acid_green"
            motion = "pan_drift"
            name = "Toxic Biohazard Protocol"
            theme = "Corrosive chemical facilities, toxic warning telemetry, high-speed lateral motion."
            typo = "warning_industrial"
            primary_override = None
            accent_override = None
            waveform_override = None
            subtitles = None
        elif any(w in lower for w in ["red", "crimson", "blood", "alarm", "danger", "breach"]):
            palette_key = "crimson_red"
            motion = "punch_climax"
            name = "Emergency Breach Directive"
            theme = "Catastrophic hull pressure alerts, intense strobe pulses, aggressive kinetic zoom punches."
            typo = "brutalist_mono"
            primary_override = None
            accent_override = None
            waveform_override = None
            subtitles = None
        elif any(w in lower for w in ["gold", "mono", "amber", "black", "white", "void", "minimal"]):
            palette_key = "monochrome_gold"
            motion = "ambient_float"
            name = "Obsidian Zero-G Void"
            theme = "Monochrome brutalist obsidian horizons, warm amber telemetry, zero-gravity floating camera."
            typo = "minimal_clean"
            primary_override = None
            accent_override = None
            waveform_override = None
            subtitles = None
        else:
            palette_key = "cyan_purple"
            motion = "push_in"
            name = "Deep Sea Cyber-Abyss"
            theme = "Bioluminescent hadal trench visuals, deep crushing sub-bass ripples, high-contrast cyan glow."
            typo = "brutalist_mono"
            primary_override = None
            accent_override = None
            waveform_override = None
            subtitles = None

        pal = COLOR_PALETTES[palette_key]
        if not subtitles:
            subtitles = [
                f"140 BPM // {album_name.upper()} // TRANSIENT LOCK",
                "144 BPM // RESONANT SUB-BASS MODULATION",
                "140 BPM // TELEMETRY LINK ESTABLISHED",
                "142 BPM // KINETIC PHASE COHERENCE",
                f"145 BPM // {album_name.upper()} // OUT NOW ON VØIDRIDE",
            ]

        return ProductionBrief(
            id=f"brief_{uuid.uuid4().hex[:8]}",
            name=name,
            theme=theme,
            color_palette=palette_key,
            primary_color=primary_override or pal["primary"],
            accent_color=accent_override or pal["accent"],
            camera_motion=motion,
            typography_style=typo,
            waveform_style=pal["waveform_style"],
            waveform_hex=waveform_override or pal["waveform_hex"],
            subtitles=subtitles,
            raw_prompt=raw_prompt,
            created_at=datetime.datetime.utcnow().isoformat() + "Z",
            is_built_in=False,
        )

    # ── Interactive Brief Tweaks ──

    def tweak_palette(self, brief: ProductionBrief, palette_key: str) -> ProductionBrief:
        """Swap the color palette and waveform colors of an existing brief."""
        if palette_key not in COLOR_PALETTES:
            palette_key = "cyan_purple"
        pal = COLOR_PALETTES[palette_key]

        return ProductionBrief(
            id=brief.id,
            name=brief.name,
            theme=brief.theme,
            color_palette=palette_key,
            primary_color=pal["primary"],
            accent_color=pal["accent"],
            camera_motion=brief.camera_motion,
            typography_style=brief.typography_style,
            waveform_style=pal["waveform_style"],
            waveform_hex=pal["waveform_hex"],
            subtitles=brief.subtitles,
            raw_prompt=brief.raw_prompt,
            created_at=brief.created_at,
            is_built_in=brief.is_built_in,
        )

    def tweak_motion(self, brief: ProductionBrief, motion_key: str) -> ProductionBrief:
        """Update camera motion style."""
        if motion_key not in CAMERA_MOTIONS:
            motion_key = "push_in"

        return ProductionBrief(
            id=brief.id,
            name=brief.name,
            theme=brief.theme,
            color_palette=brief.color_palette,
            primary_color=brief.primary_color,
            accent_color=brief.accent_color,
            camera_motion=motion_key,
            typography_style=brief.typography_style,
            waveform_style=brief.waveform_style,
            waveform_hex=brief.waveform_hex,
            subtitles=brief.subtitles,
            raw_prompt=brief.raw_prompt,
            created_at=brief.created_at,
            is_built_in=brief.is_built_in,
        )

    def tweak_typography(self, brief: ProductionBrief, typo_key: str) -> ProductionBrief:
        """Update typography and HUD presentation style."""
        if typo_key not in TYPOGRAPHY_STYLES:
            typo_key = "brutalist_mono"

        return ProductionBrief(
            id=brief.id,
            name=brief.name,
            theme=brief.theme,
            color_palette=brief.color_palette,
            primary_color=brief.primary_color,
            accent_color=brief.accent_color,
            camera_motion=brief.camera_motion,
            typography_style=typo_key,
            waveform_style=brief.waveform_style,
            waveform_hex=brief.waveform_hex,
            subtitles=brief.subtitles,
            raw_prompt=brief.raw_prompt,
            created_at=brief.created_at,
            is_built_in=brief.is_built_in,
        )
