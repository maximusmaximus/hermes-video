"""
Unit tests for MusicCatalogQuery against the hermes-music catalog.
"""

import unittest
from src.catalog.query import MusicCatalogQuery


class TestMusicCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = MusicCatalogQuery(root_dir=r"D:\music")

    def test_catalog_discovery(self):
        releases = self.catalog.list_releases()
        self.assertGreaterEqual(
            len(releases), 10, f"Expected at least 10 releases, found {len(releases)}"
        )
        slugs = [r.slug for r in releases]
        self.assertIn("chroma-morgue", slugs)

    def test_get_specific_release(self):
        release = self.catalog.get_release("chroma-morgue")
        self.assertIsNotNone(release)
        self.assertEqual(release.slug, "chroma-morgue")
        self.assertGreaterEqual(release.track_count, 5)
        self.assertIsNotNone(release.tracks)
        self.assertGreaterEqual(len(release.tracks), 5)

        first_track = release.tracks[0]
        self.assertTrue(
            "COLD_INCISION" in first_track.title or "Cold Incision" in first_track.title
        )
        self.assertTrue(first_track.audio_path.endswith(".flac"))


if __name__ == "__main__":
    unittest.main()
