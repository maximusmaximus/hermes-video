"""
src/catalog/query.py — Hermes Music Producer Catalog Bridge.

Provides unified discovery, querying, and asset selection across the VØIDRIDE
music producer catalog created by hermes-music (D:\\music and conversation e6aee6b2-72b2-47af-a580-b9ff81cb9bb9).
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


@dataclass
class TrackItem:
    id: str
    album_slug: str
    album_title: str
    title: str
    track_number: int
    audio_path: str
    duration_seconds: Optional[float] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    genre: Optional[str] = None
    stems: Optional[List[str]] = None
    cover_art_path: Optional[str] = None


@dataclass
class ReleaseItem:
    slug: str
    title: str
    label: str
    genre: str
    release_dir: str
    track_count: int
    cover_art_path: Optional[str] = None
    tracks: Optional[List[TrackItem]] = None


class MusicCatalogQuery:
    """Catalog discovery engine for VØIDRIDE music releases and stems."""

    def __init__(self, root_dir: Optional[str] = None):
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            # Check environment or default to D:\music
            env_dir = os.environ.get("MUSIC_CATALOG_DIR")
            self.root_dir = Path(env_dir) if env_dir else Path(r"D:\music")

        self.releases_dir = self.root_dir / "releases"
        self.albums_dir = self.root_dir / "albums"
        self.artwork_dir = self.root_dir / "artwork"
        self.waveform_dir = self.root_dir / "waveforms"

    def list_releases(self) -> List[ReleaseItem]:
        """Scan releases directory and return all discovered albums."""
        releases = []
        if not self.releases_dir.exists():
            return releases

        for item in sorted(self.releases_dir.iterdir()):
            if item.is_dir():
                manifest_path = item / "release.json"
                title = item.name.replace("-", " ").title()
                label = "VØIDRIDE"
                genre = "Industrial Cyberpunk / Wave"
                cover_art = None

                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            title = data.get("title", title)
                            label = data.get("label", label)
                            genre = data.get("genre", genre)
                            if "cover_art" in data:
                                cover_art = data["cover_art"]
                    except Exception:
                        pass

                # Look for cover artwork if not explicitly specified
                if not cover_art:
                    covers_dir = item / "covers"
                    if covers_dir.exists():
                        for img in covers_dir.glob("*.png"):
                            cover_art = str(img)
                            break
                        if not cover_art:
                            for img in covers_dir.glob("*.jpg"):
                                cover_art = str(img)
                                break

                # Count audio tracks
                flacs = list(item.glob("*.flac"))
                wavs = list(item.glob("*.wav"))
                total_tracks = len(flacs) if flacs else len(wavs)

                releases.append(
                    ReleaseItem(
                        slug=item.name,
                        title=title,
                        label=label,
                        genre=genre,
                        release_dir=str(item),
                        track_count=total_tracks,
                        cover_art_path=cover_art,
                    )
                )

        return releases

    def get_release(self, slug: str) -> Optional[ReleaseItem]:
        """Get full release details including all constituent tracks."""
        release_dir = self.releases_dir / slug
        if not release_dir.exists():
            return None

        manifest_path = release_dir / "release.json"
        title = slug.replace("-", " ").title()
        label = "VØIDRIDE"
        genre = "Industrial / Electronic"
        cover_art = None

        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title = data.get("title", title)
                    label = data.get("label", label)
                    genre = data.get("genre", genre)
                    cover_art = data.get("cover_art")
            except Exception:
                pass

        if not cover_art:
            covers_dir = release_dir / "covers"
            if covers_dir.exists():
                for img in list(covers_dir.glob("*.png")) + list(covers_dir.glob("*.jpg")):
                    cover_art = str(img)
                    break

        # Discover tracks
        tracks = []
        meta_path = release_dir / "tracks_meta.json"
        meta_dict = {}
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    raw_meta = json.load(f)
                    if isinstance(raw_meta, list):
                        meta_dict = {t.get("file", t.get("title", "")): t for t in raw_meta}
                    elif isinstance(raw_meta, dict):
                        meta_dict = raw_meta
            except Exception:
                pass

        audio_files = sorted(list(release_dir.glob("*.flac")) + list(release_dir.glob("*.wav")))
        for idx, audio_file in enumerate(audio_files, 1):
            t_title = audio_file.stem
            t_bpm = None
            t_key = None
            t_duration = None

            # Check if metadata was logged
            meta = meta_dict.get(audio_file.name, meta_dict.get(t_title, {}))
            if meta:
                t_title = meta.get("title", t_title)
                t_bpm = meta.get("bpm")
                t_key = meta.get("key")
                t_duration = meta.get("duration")

            tracks.append(
                TrackItem(
                    id=f"{slug}_{idx:02d}",
                    album_slug=slug,
                    album_title=title,
                    title=t_title,
                    track_number=idx,
                    audio_path=str(audio_file),
                    duration_seconds=t_duration,
                    bpm=t_bpm,
                    key=t_key,
                    genre=genre,
                    cover_art_path=cover_art,
                )
            )

        return ReleaseItem(
            slug=slug,
            title=title,
            label=label,
            genre=genre,
            release_dir=str(release_dir),
            track_count=len(tracks),
            cover_art_path=cover_art,
            tracks=tracks,
        )

    def search_tracks(
        self,
        query: Optional[str] = None,
        min_bpm: Optional[float] = None,
        max_bpm: Optional[float] = None,
    ) -> List[TrackItem]:
        """Search and filter tracks across all releases."""
        results = []
        releases = self.list_releases()
        for rel in releases:
            full_rel = self.get_release(rel.slug)
            if not full_rel or not full_rel.tracks:
                continue

            for track in full_rel.tracks:
                # Filter by query keyword
                if query:
                    q_lower = query.lower()
                    if (
                        q_lower not in track.title.lower()
                        and q_lower not in track.album_title.lower()
                        and q_lower not in (track.genre or "").lower()
                    ):
                        continue

                # Filter by BPM range
                if min_bpm and track.bpm and track.bpm < min_bpm:
                    continue
                if max_bpm and track.bpm and track.bpm > max_bpm:
                    continue

                results.append(track)

        return results


def main():
    parser = argparse.ArgumentParser(description="Hermes Music Producer Catalog Query")
    parser.add_argument("--list-albums", action="store_true", help="List all produced albums")
    parser.add_argument("--album", help="Get details for a specific album slug")
    parser.add_argument("--search", help="Search tracks by keyword")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    catalog = MusicCatalogQuery()

    if args.list_albums:
        releases = catalog.list_releases()
        if args.json:
            print(json.dumps([asdict(r) for r in releases], indent=2))
        else:
            print(f"\nDiscovered {len(releases)} albums in {catalog.releases_dir}:\n")
            for r in releases:
                print(f" • [{r.slug}] {r.title} ({r.track_count} tracks) - {r.genre}")
        return

    if args.album:
        release = catalog.get_release(args.album)
        if not release:
            print(f"Album '{args.album}' not found.")
            return
        if args.json:
            print(json.dumps(asdict(release), indent=2))
        else:
            print(f"\nAlbum: {release.title} ({release.slug})")
            print(f"Label: {release.label} | Genre: {release.genre}")
            print(f"Cover Art: {release.cover_art_path}")
            print("\nTracks:")
            for t in release.tracks or []:
                bpm_str = f"{t.bpm} BPM" if t.bpm else "BPM N/A"
                key_str = f"Key: {t.key}" if t.key else ""
                print(f"  {t.track_number:02d}. {t.title} ({bpm_str} {key_str})")
                print(f"      Path: {t.audio_path}")
        return

    if args.search:
        tracks = catalog.search_tracks(query=args.search)
        if args.json:
            print(json.dumps([asdict(t) for t in tracks], indent=2))
        else:
            print(f"\nFound {len(tracks)} matching tracks for '{args.search}':\n")
            for t in tracks:
                print(f" • {t.album_title} - {t.title} ({t.audio_path})")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
