# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VibeSport** — a sports tracking application (running distance, weight, fitness exercises) with analytics and trend reporting. Currently in the design prototyping phase. MVP targets are defined in [PRD.md](PRD.md).

## Restoring Files

All working-tree files are currently deleted. Restore from the initial commit:
```bash
git checkout 6145eb8 -- .
```

## Commands

```bash
npm install          # Install dependencies (project is bare Node.js/CommonJS skeleton)
npm test             # Placeholder — no real tests yet
```

There is no build step, dev server, or test framework yet. The "app" currently exists as standalone HTML prototypes opened directly in a browser.

## Design System

The app follows a "Fresh & Clean" aesthetic with a **strict no-animation rule** (`transition: none !important; animation: none !important;` on `*`). All state changes must be instantaneous.

| Token | Value | Usage |
|---|---|---|
| `--bg` | `oklch(0.96 0.01 160)` | Page background (near-white with mint tint) |
| `--surface` | `#ffffff` | Card/container backgrounds |
| `--fg` | `oklch(0.2 0.02 160)` | Primary text (dark charcoal) |
| `--muted` | `oklch(0.5 0.05 160)` | Secondary/muted text |
| `--border` | `oklch(0.9 0.02 160)` | Borders and dividers |
| `--accent` | `oklch(0.82 0.18 160)` | Mint green — primary accent, used max twice per screen |
| `--accent-on` | `oklch(0.2 0.02 160)` | Text color on accent backgrounds |

**Typography**: Inter (display + body), JetBrains Mono (mono/numerics/captions). All Chinese UI (`lang="zh-CN"`).

**Breakpoints**: Mobile <768px, Tablet 768–1024px, Desktop >1024px. Prototypes use a single 920px media query for mobile reflow.

## Prototype Architecture

Each prototype is a **self-contained single HTML file** with embedded CSS. They share a consistent structure:

- **`:root` CSS custom properties** for the design tokens above
- **Grid-based app shell**: `grid-template-columns: 260px 1fr` (sidebar + main) for dashboard views
- **Persistent sticky topnav** with brand dot (`.brand-dot` — 12px accent circle), brand name, and nav links
- **Card-based content**: KPI stat cards, log entry cards, form cards — all using `--surface` with `--border`
- **Sidebar nav** with icon+label items, active state highlighted with accent left-border

### Prototype Files

| File | Purpose |
|---|---|
| `vibesport-landing.html` | Marketing landing page (hero, features, CTA) |
| `vibesport-landing-2.html` | Refined landing with `--elev-raised` and `--focus-ring` tokens |
| `vibesport-login.html` | Auth page (centered card with email + password form) |
| `vibesport-home.html` | Dashboard (sidebar nav, KPI cards, recent activity log, quick-add FAB) |

## Open Design Skills (`.od-skills/`)

The project uses Open Design skills that guide prototype creation:

- **`web-prototype`**: Primary skill for generating new HTML prototypes. Workflow: read `template.html` seed → pick layouts from `references/layouts.md` → paste sections → fill copy → self-check against `references/checklist.md`. Mandates single accent per screen, serif display fonts, `.ph-img` placeholders (never external URLs), and `data-od-id` on every `<section>`.
- **`impeccable-design-polish`**: Post-generation polish pass. Removes AI tells (generic 3-card rows, oversized rounded corners, empty marketing adjectives, purple-blue glow gradients), adds restrained motion if needed, hardens responsive/accessibility issues.
- **`creative-director`**: Design critique and direction.
- **`agent-browser`**: Browser automation for QA, screenshot capture, accessibility checks on prototypes.

## PRD Architecture Direction (Future)

The backend will be Node.js/CommonJS with these data models:

- **User**: `user_id` (UUID PK), `username`, `email`, `password_hash`, `created_at`
- **RunningLogs**: `log_id`, `user_id` (FK), `distance_km` (Decimal), `date`, `notes`
- **FitnessLogs**: `fitness_id`, `user_id` (FK), `exercise_type`, `duration_minutes`, `reps_sets`, `date`
- **WeightLogs**: `weight_id`, `user_id` (FK), `weight_value` (Decimal), `date`

MVP roadmap: Foundation (auth + schema) → Data Entry (CRUD forms) → Analytics (stats + reports) → Polish (final UI + QA). Target: <1.5s page loads, WCAG 2.1 AA, responsive across all breakpoints.
