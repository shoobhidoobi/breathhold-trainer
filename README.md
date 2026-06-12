# breathhold-trainer

A simple, stateless web app for breathhold training using CO₂ and O₂ tables.

## How it works

1. Enter your personal best breathhold time.
2. Pick a table type:
   - **CO₂ table** — fixed holds (~50% of PB), rests shrink each round. Builds CO₂ tolerance.
   - **O₂ table** — fixed rests, holds grow from ~40% to ~80% of PB. Builds O₂ efficiency.
3. Each session is slightly randomised, so no two sessions are identical.
4. Follow the guided timer with audio cues through 8 rounds.

No accounts, no storage, no backend — just open `index.html` in a browser.

## Run locally

```sh
open index.html        # or just double-click it
```

## Safety

Never train breathholds in water alone. Stop immediately if you feel dizzy or unwell.
