# breathhold-trainer

A simple, stateless web app for breathhold training using CO₂ and O₂ tables.

## How it works

1. Enter your personal best breathhold time.
2. Pick a table type:
   - **CO₂ table** — fixed holds (~50–60% of PB), rests shrink from ~2 min down to ~15–30 s in equal steps. Builds CO₂ tolerance.
   - **O₂ table** — fixed ~2 min rests, holds grow in equal steps from ~50% to ~80% of PB. Builds O₂ efficiency.
3. Each session is slightly randomised, so no two sessions are identical.
4. Follow the guided timer with audio cues through 8 rounds.

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
