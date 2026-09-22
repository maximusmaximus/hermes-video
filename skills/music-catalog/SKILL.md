---
name: music-catalog
description: Search and select tracks, master FLACs, stems, waveforms, and artwork from the VØIDRIDE music producer catalog (D:\music).
---

# Music Catalog Skill

Provides the Hermes agent with deep query access to the music producer catalog generated at `e6aee6b2-72b2-47af-a580-b9ff81cb9bb9`.

## Usage

Agents can run `python -m src.catalog.query` from the repository root:

```sh
# List all 19+ available albums
python -m src.catalog.query --list-albums

# Inspect an album and its constituent tracks, BPM, and stems
python -m src.catalog.query --album chroma-morgue

# Search for specific tracks or subgenres
python -m src.catalog.query --search "industrial phonk"
```

## Python Integration

```python
from src.catalog.query import MusicCatalogQuery

catalog = MusicCatalogQuery()
releases = catalog.list_releases()
track = catalog.search_tracks(query="COLD INCISION")[0]
print(track.audio_path, track.bpm, track.key)
```
