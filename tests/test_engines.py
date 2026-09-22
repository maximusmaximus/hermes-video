"""
Unit tests for the Tesseract and Video Engines.
"""

import os
import unittest
import tempfile
from pathlib import Path

from src.engines.base import VideoProjectSpec
from src.engines.tesseract import TesseractEngine


class TestVideoEngines(unittest.TestCase):
    def test_tesseract_availability(self):
        engine = TesseractEngine()
        available = engine.is_available()
        self.assertTrue(available, f"Tesseract CLI not available at {engine.cli_path}")
        version = engine.get_version()
        self.assertIsNotNone(version)
        self.assertIn("0.1.0", version)

    def test_tesseract_create_project(self):
        engine = TesseractEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_unit.tsrct"
            spec = VideoProjectSpec(
                name="Unit Test Project",
                width=1920,
                height=1080,
                duration=5.0,
            )
            res = engine.create_project(spec, str(project_path))
            self.assertTrue(res.success, f"Create project failed: {res.error}")
            self.assertTrue(project_path.exists())


if __name__ == "__main__":
    unittest.main()
