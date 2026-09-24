"""
tests/test_prompt_templates_e2e.py — Comprehensive End-to-End Test Suite.

Covers:
1. ProductionBrief & TemplateManager (CRUD, persistence, built-ins, custom storage)
2. PromptUpscaler (Heuristic fallback, keyword routing, Venice API parsing, BudgetLedger integration)
3. Interactive Parameter Tweaks (Palette, Motion, Typography adjustments)
4. MotionDirector Brief Injection (HUD colors, waveform styling, dynamic subtitles)
5. Daemon Workflow Simulation (Menu navigation, prompt injection, template load/save, production launch)
"""

import os
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.budget.ledger import BudgetLedger
from src.templates.manager import ProductionBrief, TemplateManager, BUILTIN_TEMPLATES
from src.storyboard.prompt_upscaler import (
    PromptUpscaler,
    COLOR_PALETTES,
    CAMERA_MOTIONS,
    TYPOGRAPHY_STYLES,
)
from src.engines.motion_director import MotionDirector, _hex_to_rgb
from src.telegram.daemon import TelegramBotDaemon


class TestTemplateManager(unittest.TestCase):
    """Test suite for style template persistence and management."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.storage_file = Path(self.tmpdir.name) / "templates.json"
        self.manager = TemplateManager(storage_path=str(self.storage_file))

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_builtin_templates_initialized(self):
        templates = self.manager.list_templates()
        self.assertGreaterEqual(len(templates), 4)
        builtin_ids = [t.id for t in templates if t.is_built_in]
        self.assertIn("tpl_cyberpunk_sea", builtin_ids)
        self.assertIn("tpl_industrial_acid", builtin_ids)
        self.assertIn("tpl_crimson_breach", builtin_ids)
        self.assertIn("tpl_monochrome_void", builtin_ids)

    def test_save_and_retrieve_custom_template(self):
        brief = ProductionBrief(
            id="",
            name="Neon Plasma Storm",
            theme="High-voltage purple lightning across obsidian monoliths",
            color_palette="cyan_purple",
            primary_color="#9900ff",
            accent_color="#00ffff",
            camera_motion="punch_climax",
            typography_style="warning_industrial",
            waveform_style="cyan",
            waveform_hex="0x00ffff",
            subtitles=["150 BPM // PLASMA DISCHARGE", "150 BPM // VOLTAGE PEAK"],
            raw_prompt="Purple lightning and high voltage",
        )
        saved = self.manager.save_template(brief, name="Neon Plasma Storm")
        self.assertTrue(saved.id.startswith("custom_"))
        self.assertFalse(saved.is_built_in)

        # Retrieve by ID
        fetched = self.manager.get_template(saved.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Neon Plasma Storm")
        self.assertEqual(fetched.primary_color, "#9900ff")
        self.assertEqual(fetched.waveform_hex, "0x00ffff")

    def test_delete_custom_template(self):
        brief = ProductionBrief(
            id="custom_test_123",
            name="Temporary Template",
            theme="Temp theme",
            color_palette="acid_green",
            primary_color="#39ff14",
            accent_color="#00ffcc",
            camera_motion="pan_drift",
            typography_style="brutalist_mono",
            waveform_style="green",
            waveform_hex="0x39ff14",
            is_built_in=False,
        )
        self.manager.save_template(brief)
        self.assertIsNotNone(self.manager.get_template("custom_test_123"))

        # Delete it
        success = self.manager.delete_template("custom_test_123")
        self.assertTrue(success)
        self.assertIsNone(self.manager.get_template("custom_test_123"))

    def test_cannot_delete_builtin_template(self):
        success = self.manager.delete_template("tpl_cyberpunk_sea")
        self.assertFalse(success)
        self.assertIsNotNone(self.manager.get_template("tpl_cyberpunk_sea"))


class TestPromptUpscaler(unittest.TestCase):
    """Test suite for Venice AI prompt upscaler and heuristic fallback."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test_budget.db"
        self.budget = BudgetLedger(db_path=str(db_path))
        # Use api_key=None for instant heuristic tests
        self.upscaler = PromptUpscaler(budget_ledger=self.budget, api_key=None)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_heuristic_keyword_acid_green(self):
        prompt = "Toxic biohazard radioactive chemical facility with high speed cuts"
        brief = self.upscaler._heuristic_fallback(prompt, "Chroma Morgue", None, "Industrial")
        self.assertEqual(brief.color_palette, "acid_green")
        self.assertEqual(brief.primary_color, "#39ff14")
        self.assertEqual(brief.waveform_hex, "0x39ff14")
        self.assertEqual(brief.camera_motion, "pan_drift")
        self.assertEqual(len(brief.subtitles), 5)

    def test_heuristic_keyword_crimson_red(self):
        prompt = "Emergency red alarm strobe pressure breach with heavy explosive drops"
        brief = self.upscaler._heuristic_fallback(prompt, "Abyss Throttle", None, "Cyberpunk")
        self.assertEqual(brief.color_palette, "crimson_red")
        self.assertEqual(brief.primary_color, "#ff003c")
        self.assertEqual(brief.waveform_hex, "0xff003c")
        self.assertEqual(brief.camera_motion, "punch_climax")

    def test_heuristic_keyword_mars_mad_max(self):
        prompt = "Make a crazy mars landing is dramatic, aliens and think horror movie but with burning man mad max vibes"
        brief = self.upscaler._heuristic_fallback(prompt, "Mars Descent", "APOGEE_DRIFT", "Industrial")
        self.assertEqual(brief.color_palette, "crimson_red")
        self.assertEqual(brief.primary_color, "#ff3300")
        self.assertEqual(brief.camera_motion, "punch_climax")
        self.assertIn("Martian", brief.name)

    def test_heuristic_keyword_xenomorph_horror(self):
        prompt = "Deep space alien horror dread with xenomorph nightmare creature"
        brief = self.upscaler._heuristic_fallback(prompt, "Cryoclastic Zero", None, "Dark Ambient")
        self.assertEqual(brief.color_palette, "acid_green")
        self.assertEqual(brief.primary_color, "#39ff14")
        self.assertEqual(brief.camera_motion, "punch_climax")
        self.assertIn("Horror", brief.name)

    def test_heuristic_keyword_monochrome_void(self):
        prompt = "Stark minimal obsidian void with warm amber gold telemetry"
        brief = self.upscaler._heuristic_fallback(prompt, "Sigil Engine", None, "Dark Ambient")
        self.assertEqual(brief.color_palette, "monochrome_gold")
        self.assertEqual(brief.primary_color, "#ffffff")
        self.assertEqual(brief.waveform_hex, "0xffb000")
        self.assertEqual(brief.camera_motion, "ambient_float")

    def test_tweak_palette(self):
        base_brief = self.upscaler.upscale_prompt("Deep sea ocean trench", "Abyss Throttle")
        self.assertEqual(base_brief.color_palette, "cyan_purple")

        # Tweak to acid green
        tweaked = self.upscaler.tweak_palette(base_brief, "acid_green")
        self.assertEqual(tweaked.color_palette, "acid_green")
        self.assertEqual(tweaked.primary_color, "#39ff14")
        self.assertEqual(tweaked.waveform_hex, "0x39ff14")
        self.assertEqual(tweaked.camera_motion, base_brief.camera_motion)

    def test_tweak_motion(self):
        base_brief = self.upscaler.upscale_prompt("Deep sea ocean trench", "Abyss Throttle")
        tweaked = self.upscaler.tweak_motion(base_brief, "ambient_float")
        self.assertEqual(tweaked.camera_motion, "ambient_float")
        self.assertEqual(tweaked.primary_color, base_brief.primary_color)

    @patch("urllib.request.urlopen")
    def test_mock_venice_upscale_success(self, mock_urlopen):
        self.upscaler.api_key = "mock_key"
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "name": "Abyssal Singularity",
                            "theme": "Superheated hydrothermal vents tearing through obsidian bedrock",
                            "color_palette": "crimson_red",
                            "primary_color": "#ff003c",
                            "accent_color": "#ff8800",
                            "camera_motion": "punch_climax",
                            "typography_style": "brutalist_mono",
                            "waveform_style": "red",
                            "waveform_hex": "0xff003c",
                            "subtitles": [
                                "140 BPM // CRITICAL PRESSURE SPIKE",
                                "142 BPM // THERMAL SHOCK OVERDRIVE",
                                "140 BPM // HYDROTHERMAL VENT LOCK",
                                "144 BPM // ACOUSTIC CAVITATION DETECTED",
                                "145 BPM // CATACLYSM // OUT NOW ON VØIDRIDE",
                            ]
                        })
                    }
                }
            ],
            "usage": {"prompt_tokens": 1200, "completion_tokens": 400}
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        brief = self.upscaler.upscale_prompt("Hydrothermal vent tearing open", "Abyss Throttle")
        self.assertEqual(brief.name, "Abyssal Singularity")
        self.assertEqual(brief.color_palette, "crimson_red")
        self.assertEqual(brief.primary_color, "#ff003c")
        self.assertEqual(len(brief.subtitles), 5)

        # Verify spend was recorded in BudgetLedger
        summary = self.budget.get_budget_summary()
        self.assertGreater(summary["controller_used_usd"], 0.0)


class TestMotionDirectorBriefInjection(unittest.TestCase):
    """Test suite for MotionDirector parameter and brief injection."""

    def setUp(self):
        self.motion = MotionDirector()
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_hex_to_rgb(self):
        self.assertEqual(_hex_to_rgb("#00f0ff"), (0, 240, 255))
        self.assertEqual(_hex_to_rgb("0x39ff14"), (57, 255, 20))
        self.assertEqual(_hex_to_rgb("#ff003c"), (255, 0, 60))
        self.assertEqual(_hex_to_rgb("invalid"), (0, 240, 255))

    def test_create_hud_overlay_with_custom_colors(self):
        out_png = Path(self.tmpdir.name) / "test_hud.png"
        self.motion.create_hud_overlay(
            output_png=str(out_png),
            width=1080,
            height=1920,
            album_title="Abyss Throttle",
            track_number=1,
            total_tracks=5,
            track_title="Hadal Trench",
            metadata_line="140 BPM // D# MINOR",
            catalog_code="VØID-019",
            primary_color="#39ff14",
            accent_color="#00ffcc",
        )
        self.assertTrue(out_png.exists())
        self.assertGreater(out_png.stat().st_size, 5000)

    def test_create_hud_overlay_with_custom_headers(self):
        out_png = Path(self.tmpdir.name) / "test_hud_track.png"
        self.motion.create_hud_overlay(
            output_png=str(out_png),
            width=1080,
            height=1080,
            album_title="Mars Descent",
            track_number=1,
            total_tracks=5,
            track_title="Apogee Drift",
            metadata_line="145 BPM // D# MINOR",
            catalog_code="VØID-019",
            primary_color="#ff3300",
            accent_color="#ff8800",
            subtitle_header="MARS DESCENT — OFFICIAL TRACK VISUALIZER",
            style_tag="Martian Firestorm",
        )
        self.assertTrue(out_png.exists())
        self.assertGreater(out_png.stat().st_size, 5000)


class TestDaemonWorkflowIntegration(unittest.TestCase):
    """Test suite for TelegramBotDaemon prompt injection & template studio flow."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test_budget.db"
        tpl_path = Path(self.tmpdir.name) / "test_templates.json"

        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "mock_token",
            "TELEGRAM_CHAT_ID": "8293122782",
            "VENICE_CONTROLLER_KEY": "",
        }):
            self.daemon = TelegramBotDaemon(enforce_single=False)
            self.daemon.budget = BudgetLedger(db_path=str(db_path))
            self.daemon.template_manager = TemplateManager(storage_path=str(tpl_path))
            self.daemon.upscaler = PromptUpscaler(budget_ledger=self.daemon.budget, api_key="")

        # Mock outgoing Telegram API calls
        self.daemon._call = MagicMock(return_value={"ok": True, "result": {"message_id": 9999}})

    def tearDown(self):
        self.daemon.executor.shutdown(wait=True)
        try:
            self.tmpdir.cleanup()
        except Exception:
            pass

    def test_pmenu_routes_to_studio(self):
        cb = {
            "id": "cb_1",
            "data": "pmenu:abyss-throttle:9_16:0",
            "message": {"message_id": 100},
        }
        self.daemon.handle_callback_query(cb)
        self.daemon._call.assert_any_call(
            "answerCallbackQuery",
            {"callback_query_id": "cb_1", "text": "🎨 Opening Production Studio...", "show_alert": False},
            timeout=4,
        )

    def test_ask_p_sets_awaiting_state(self):
        cb = {
            "id": "cb_2",
            "data": "ask_p:abyss-throttle:9_16:0",
            "message": {"message_id": 100},
        }
        self.daemon.handle_callback_query(cb)
        state = self.daemon.user_states.get("8293122782")
        self.assertIsNotNone(state)
        self.assertEqual(state["action"], "awaiting_prompt")
        self.assertEqual(state["slug"], "abyss-throttle")
        self.assertEqual(state["ratio"], "9_16")

    def test_handle_message_upscales_prompt(self):
        import time

        # Set awaiting prompt state
        self.daemon.user_states["8293122782"] = {
            "action": "awaiting_prompt",
            "slug": "abyss-throttle",
            "ratio": "9_16",
            "track_num": 0,
            "message_id": 100,
        }

        # User sends text
        msg = {
            "text": "Toxic acid green chemical reactor with flashing strobe alerts",
            "from": {"username": "tester", "first_name": "Tester"},
        }
        self.daemon.handle_message(msg)

        # Wait briefly for worker thread to finish
        session_key = "abyss-throttle:9_16:0"
        for _ in range(30):
            if session_key in self.daemon.active_briefs:
                break
            time.sleep(0.05)

        # State should be cleared
        self.assertNotIn("8293122782", self.daemon.user_states)

        # Active brief should be stored
        brief = self.daemon.active_briefs.get(session_key)
        self.assertIsNotNone(brief)
        self.assertEqual(brief.color_palette, "acid_green")
        self.assertEqual(brief.primary_color, "#39ff14")

        # Automatically persisted as custom template
        saved_templates = self.daemon.template_manager.list_templates()
        custom = [t for t in saved_templates if not t.is_built_in]
        self.assertGreaterEqual(len(custom), 1)

    def test_set_pal_callback(self):
        session_key = "abyss-throttle:9_16:0"
        self.daemon._get_active_brief("abyss-throttle", "9_16", 0)

        cb = {
            "id": "cb_3",
            "data": "set_pal:abyss-throttle:9_16:0:crimson_red",
            "message": {"message_id": 100},
        }
        self.daemon.handle_callback_query(cb)
        brief = self.daemon.active_briefs.get(session_key)
        self.assertEqual(brief.color_palette, "crimson_red")
        self.assertEqual(brief.primary_color, "#ff003c")

    def test_save_and_apply_template_callback(self):
        session_key = "abyss-throttle:9_16:0"
        brief = self.daemon._get_active_brief("abyss-throttle", "9_16", 0)
        brief.name = "My Saved Custom Style"

        # Save template
        cb_save = {
            "id": "cb_save",
            "data": "save_tpl:abyss-throttle:9_16:0",
            "message": {"message_id": 100},
        }
        self.daemon.handle_callback_query(cb_save)

        saved_templates = self.daemon.template_manager.list_templates()
        custom_saved = next((t for t in saved_templates if t.name == "My Saved Custom Style"), None)
        self.assertIsNotNone(custom_saved)

        # Apply another template
        cb_apply = {
            "id": "cb_apply",
            "data": "apply_tpl:abyss-throttle:9_16:0:tpl_industrial_acid",
            "message": {"message_id": 100},
        }
        self.daemon.handle_callback_query(cb_apply)
        active = self.daemon.active_briefs.get(session_key)
        self.assertEqual(active.id, "tpl_industrial_acid")
        self.assertEqual(active.color_palette, "acid_green")

    def test_launch_prod_autosaves_custom_brief(self):
        session_key = "mars-descent:1_1:1"
        brief = ProductionBrief(
            id="brief_unsaved_123",
            name="Apocalyptic Mars Teaser",
            theme="Dramatic Mars landing",
            color_palette="crimson_red",
            primary_color="#ff3300",
            accent_color="#ff8800",
            camera_motion="punch_climax",
            typography_style="warning_industrial",
            waveform_style="red",
            waveform_hex="0xff3300",
            subtitles=["145 BPM // MARS ENTRY"],
            is_built_in=False,
        )
        self.daemon.active_briefs[session_key] = brief

        with patch.object(self.daemon.executor, "submit") as mock_submit:
            cb = {
                "id": "cb_launch",
                "data": "launch_prod:mars-descent:1_1:1:active",
                "message": {"message_id": 100},
            }
            self.daemon.handle_callback_query(cb)
            mock_submit.assert_called_once()

        # Brief should now be saved in template manager
        saved = [t for t in self.daemon.template_manager.list_templates() if t.name == "Apocalyptic Mars Teaser"]
        self.assertEqual(len(saved), 1)
        self.assertTrue(saved[0].id.startswith("custom_"))


if __name__ == "__main__":
    unittest.main()
