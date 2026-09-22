# System Architecture: Hermes Video Agent (`hermes-video`)

The `hermes-video` system connects autonomous LLM reasoning, deep music catalog integration, local GPU-accelerated video rendering, and remote Telegram/Cloudflare human-in-the-loop review.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        HERMES VIDEO CONTROLLER                         │
│                                                                        │
│   ┌─────────────────────┐                 ┌────────────────────────┐   │
│   │ Music Catalog Query │                 │  Budget Ledger Enforce │   │
│   │ (D:\music Releases) │                 │  ($1/day Controller)   │   │
│   └──────────┬──────────┘                 └───────────┬────────────┘   │
│              │                                        │                │
│              ▼                                        ▼                │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │               Storyboard & Kinetic Text Director               │   │
│   │               (docs/video-standards.md standards)              │   │
│   └──────────────────────────────┬─────────────────────────────────┘   │
└──────────────────────────────────┼─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        MODULAR VIDEO ENGINES                           │
│                                                                        │
│   ┌───────────────────────────┐           ┌────────────────────────┐   │
│   │   Tesseract by Mirage     │           │   Extensible Adapters  │   │
│   │   (Local tsrct CLI 0.1.0) │           │   (ComfyUI / Runway)   │   │
│   │   • tesseract-video       │           │   • Future cloud AI    │   │
│   │   • tesseract-motion      │           │     video generators   │   │
│   └─────────────┬─────────────┘           └────────────────────────┘   │
└─────────────────┼──────────────────────────────────────────────────────┘
                  │
                  ▼ Rendered Video / .tsrct Document
┌────────────────────────────────────────────────────────────────────────┐
│                        REVIEW & DECISION GATES                         │
│                                                                        │
│   ┌───────────────────────────┐           ┌────────────────────────┐   │
│   │ Cloudflare Tunnel Bridge  │           │   Telegram Gateway     │   │
│   │ (secure-share / 8124)     │──────────▶│   (Inline Buttons)     │   │
│   │ https://*.trycloudflare   │           │   Chat: 8293122782     │   │
│   └───────────────────────────┘           └────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

## Inference Budget Architecture

To ensure operational efficiency and cost predictability:
- **Total Pool**: **$5.00 / day** maximum across all Venice AI services.
- **Controller Agent**: **$1.00 / day** maximum dedicated to scriptwriting, beat-mapping, and Tesseract layer generation.
- **Worker Allocation**: **$4.00 / day** remaining pool available for generative visual frames or prompt enhancements.
- **Pre-flight Enforcement**: Before every request, `src/budget/ledger.py` queries a rolling 24-hour window in SQLite (`data/budget.db`). If `current_usage + estimated_cost > daily_limit`, the pipeline halts gracefully.
