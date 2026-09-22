# Video Production & Description Standards

This document establishes the official standard practices for planning, describing, pacing, and rendering videos within the `hermes-video` ecosystem. These standards govern both human operators and autonomous agents (Hermes Controller, Tesseract Director).

---

## 1. Editorial Hierarchy & Narrative Pacing

Every video must follow a deliberate editorial arc rather than a generic sequence of cuts:

```
[0:00 - 0:03] THE HOOK
  ↳ Maximum impact visual + audio transient arrival.
  ↳ Establish proposition, mood, or sonic tension immediately.
  ↳ Zero filler / dead air.

[0:03 - 0:15] PHRASE PROGRESSION
  ↳ Introduce primary footage or native motion graphic scene.
  ↳ Match visual arrivals to musical downbeats (bars 1, 5, 9).
  ↳ Micro-SFX on structural transitions.

[0:15 - 0:45] CLIMAX / CORE THEME
  ↳ Peak kinetic density: rapid montage, punch-ins, or layered motion typography.
  ↳ Frequency-synced modulation (e.g. scale punch on 808/kick hits).

[0:45 - END] RESOLUTION & OUTRO
  ↳ Brand mark / track identification / release artifact.
  ↳ Reverb tail decay or fade to black aligned with master audio ending.
```

---

## 2. Music & Waveform-Synced Editing

Music is not background audio; it is the **temporal clock** of the edit.

### Synchronization Rules
1. **Cut on Transients or Leading Anticipation**:
   - For high-energy cuts (kick, snare, drop): place the cut **2 frames before** the audio peak transient. The human visual processing lag (~80ms) makes cuts landing 2 frames ahead feel intuitively tighter than cuts directly on or after the beat.
2. **Phrase-Level Pacing**:
   - Align scene transitions with musical phrases (every 4 or 8 bars). Never make a major scene change mid-phrase unless intentionally creating disruptive syncopation.
3. **Stem-Aware Visual Layering**:
   - **Main / Drums**: Drives hard cuts, camera shakes, glitch transitions, and punch-ins.
   - **Bass / Sub**: Drives scale pulses, color saturation blooms, or subtle heat refraction effects.
   - **Synths / Leads**: Drives kinetic typography reveals and motion trajectory sweeps.
   - **Atmosphere / FX**: Drives background ambient particles, smoke, and lighting fades.

---

## 3. Standardized Scene Description Schema

When generating, requesting, or cataloging footage and video scenes, all prompts and briefs must adhere to the **6-Vector Scene Schema**:

```yaml
scene:
  id: "scene_01"
  timestamp: "00:00.000 - 00:03.200"
  framing: "Extreme Close-Up (ECU) | Wide Shot (WS) | Medium Close-Up (MCU)"
  camera_movement: "Slow push-in along Z-axis (2.5% scale/sec) with subtle Dutch angle (+3°)"
  lighting_atmosphere: "High-contrast chiaroscuro, volumetric Cherenkov blue backlighting, deep crushed shadows"
  subject_action: "Circuit traces illuminate rhythmically in sync with 140 BPM synth pulse"
  color_grade_lut: "VØIDRIDE Industrial Cold: Teal/Cyan highlights (#00f0ff), deep carbon black (#0a0a0e)"
  native_fx: "Heat refraction layer with 15% edge aberration, motion blur shutter angle 180°"
```

### Prompt Construction Guidelines
- **Avoid Vague Modifiers**: Do not use "cinematic", "photorealistic", or "cool".
- **Specify Physics and Mechanics**: Describe lens focal length (e.g., `35mm anamorphic`), aperture depth (`f/1.8 shallow DOF`), and lighting source (`neon amber practical rim light`).
- **Define Screen Velocity**: Specify speed (e.g., `accelerates from rest to 1200px/s across 18 frames`).

---

## 4. Continuity & Eyeline Rules

When cutting between takes, angles, or scenes:
1. **Eyeline Continuity**:
   - In talking-head or subject-focused clips, align the subject's eye height across cuts within the top third grid line.
2. **Punch-In Limit (Digital Zoom)**:
   - Cap digital punch-ins at **115% to 125%** of source resolution to prevent pixel smearing and artifact distortion.
3. **180-Degree Rule**:
   - Maintain consistent camera orientation across directional movements to preserve viewer spatial orientation.

---

## 5. Motion Graphics & Kinetic Typography

Tesseract renders native vector text and shape layers locally. Follow these animation standards:

1. **Easing Functions**:
   - Never use linear interpolation (`Linear`).
   - Default to **Cubic Bezier Ease-Out** (`ease_out_cubic` or `[0.25, 1.0, 0.5, 1.0]`) for incoming text.
   - Use **Overshoot / Spring** (`ease_out_back`) for UI popups, badge reveals, and metric callouts.
2. **Readability & Timing**:
   - **Single Word Callout**: Minimum 18 frames (0.6s at 30fps).
   - **Short Phrase (3-5 words)**: Minimum 45 frames (1.5s).
   - **Full Sentence / Track Title**: Minimum 75 frames (2.5s).
3. **Typography Styling**:
   - Monospace or Brutalist sans-serif (e.g., *JetBrains Mono*, *Syne*, *Inter Tight*).
   - All uppercase for technical telemetry, release metadata, and VØIDRIDE track aesthetics.
   - Tracking: +0.05em to +0.15em for high-tech legibility.

---

## 6. Aspect Ratio & Delivery Profiles

| Profile | Dimensions | Aspect Ratio | Target Platform | Primary Use Case |
|---------|------------|--------------|-----------------|------------------|
| **Landscape 4K** | 3840 × 2160 | 16:9 | YouTube, Vimeo, Desktop | Full music video, master release, official visualizer |
| **Landscape HD** | 1920 × 1080 | 16:9 | Broadcast, Web | Standard delivery, low-latency review previews |
| **Vertical Reel** | 1080 × 1920 | 9:16 | TikTok, IG Reels, YT Shorts | Single teasers, stem breakdowns, drop previews |
| **Square Feed** | 1080 × 1080 | 1:1 | Instagram Feed, Telegram | Track release cards, album artwork motion loops |

---

## 7. Review & Quality Control Gate

Before presenting any render to the user via Telegram:
1. **Waveform Drift Check**: Ensure video frame 0 aligns exactly with audio sample 0.
2. **Safe Margin Compliance**: Keep text within the 90% title-safe area (especially for 9:16 where platform UI overlays obscure edges).
3. **Codec & Compression**: Export previews with fast H.264/AAC encoding for instant mobile playback over Cloudflare tunnels; export master archival copies in ProRes 4444 or visually lossless H.265 (CRF 16).

---

## 8. Master Audio Muxing & Deliverable Packaging

Raw render engines (like Tesseract CLI `tsrct export`) output video frames without audio. The video workflow must never present silent video or raw project descriptor files (`.tsrct`) as final deliverables.

1. **Mandatory Master Audio Mux**:
   - Always mux the master 24-bit/48kHz FLAC from `D:\music` into the exported MP4 using FFmpeg:
     ```bash
     ffmpeg -y -i raw_video.mp4 -i master.flac -c:v copy -c:a aac -b:a 320k -shortest final_master.mp4
     ```
2. **Telegram Direct Deliverable (`sendVideo`)**:
   - Send the final `.mp4` file directly to the user's Telegram chat so it renders in the native Telegram video player with inline sound and waveform controls.
3. **Cloudflare Tunnel Web Distribution**:
   - Simultaneously package the render via `secure-share` (`cloudflared`) and attach an interactive `⚡ Stream via Cloudflare Tunnel` button linking to the temporary `trycloudflare.com` URL.

---

## 9. Telegram Responsiveness & Telemetry Lifecycle

High responsiveness is mandatory for human-in-the-loop autonomous direction:

1. **Zero-Latency Toast Acknowledgment (<50ms)**:
   - The daemon must invoke `answerCallbackQuery` immediately upon receiving any button press. Never let the mobile client linger with a loading spinner.
2. **Asynchronous Execution Threading**:
   - Offload long-running render jobs to a background `ThreadPoolExecutor`. The Telegram polling loop must never block on video exports or network uploads.
3. **Four-Phase Milestone Telemetry**:
   - **Phase 1: Audio Analysis**: Report BPM, musical key, transient phrase grid, and FLAC source integrity.
   - **Phase 2: Storyboard & Typography**: Detail scene timings, typography layout, camera movement, and Venice controller inference spend.
   - **Phase 3: Render Preview Frame**: Extract and dispatch frame 0 (`tsrct preview --time 0.0`) via `sendPhoto` for immediate visual confirmation.
   - **Phase 4: Deliverable & Action Gate**: Dispatch final video player with Cloudflare stream and 4K finalization buttons.
