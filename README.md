# breathhold-trainer

A simple, stateless web app for breathhold training using CO₂ and O₂ tables.

## How it works

1. Enter your personal best breathhold time.
2. Pick a table type:
   - **CO₂ table** — fixed holds (~50–60% of PB), rests shrink from ~2 min down to ~15–30 s in equal steps. Builds CO₂ tolerance.
   - **O₂ table** — fixed ~2 min rests, holds grow in equal steps from ~50% to ~80% of PB. Builds O₂ efficiency.
3. Pick voice guidance: **Full** (guides every phase — close your eyes and follow along), **Minimal** (phase changes and final-breath warning only), or **Off** (beeps only).
4. Each session is slightly randomised, so no two sessions are identical.
5. Follow the guided timer through 8 rounds — with Full voice guidance you can complete the whole session eyes-closed.

Voice prompts use the browser's built-in speech synthesis (no network needed); beeps mark the precise second. A screen wake lock keeps your phone awake during the session where supported.

No accounts, no storage, no backend — just open `index.html` in a browser.

## Run locally

```sh
open index.html        # or just double-click it
```

## Tests

Fuzz-style e2e tests (Playwright) covering table generation, edge-case inputs, timer flow, and mobile layout:

```sh
pip install playwright && playwright install chromium
python tests/fuzz_test.py
```

## Safety

Never train breathholds in water alone. Stop immediately if you feel dizzy or unwell.
