# Tesseract by Mirage: Local Video Engine Guide

[Tesseract](https://github.com/mirage-hq/Tesseract) is a local creative suite engineered specifically for AI agents to edit footage, author native motion graphics, and mix audio in a connected `.tsrct` project document.

## System Compatibility
- **Windows**: 64-bit Windows 10/11 on `AMD64` architecture.
- **macOS**: Apple Silicon (`arm64`) and Intel (`x86_64`).
- **Linux/WSL**: Not supported for local execution.

## Installed CLI Specification
- **Version**: `0.1.0` (pinned)
- **Executable Location**: `%LOCALAPPDATA%\Tesseract\bin\tsrct.cmd`
- **Core Binary**: `%LOCALAPPDATA%\Tesseract\public-cli\0.1.0-x86_64\bin\tsrct.exe`
- **Verification Hash**: `36becb731f7fdeeedbd6beac75aff54eec11b1801583c2623b72d4fff3da8923`

## CLI Commands

### 1. Create a Project
```cmd
tsrct project create --project path\to\my_project.tsrct
```

### 2. Render Single Frame Preview
```cmd
tsrct preview --project path\to\my_project.tsrct --time 00:02.500 --output preview.png
```

### 3. Render Filmstrip Grid
```cmd
tsrct filmstrip --project path\to\my_project.tsrct --output filmstrip.png --max-frames 9 --items-per-row 3
```

### 4. Export Video
```cmd
tsrct export --project path\to\my_project.tsrct --output output.mp4
```

## Agent Skills Installed
1. **`tesseract-video`**: Cuts, dialogue pacing, waveform sync, eyeline continuity, audio mix.
2. **`tesseract-motion`**: Native keyframe motion, cubic bezier easing, kinetic typography, shapes.
