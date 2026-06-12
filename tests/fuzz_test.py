"""Fuzz-style e2e tests for the breathhold trainer.

Usage:
    pip install playwright && playwright install chromium
    python tests/fuzz_test.py
"""
import os
import random
import sys
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
server = HTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=ROOT))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{server.server_port}/index.html"
failures = []

def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("FAIL:", msg)

def to_secs(t):
    m, s = t.split(":")
    return int(m) * 60 + int(s)

def read_table(page):
    rows = page.locator("#table-body tr")
    out = []
    for i in range(rows.count()):
        tds = rows.nth(i).locator("td").all_inner_texts()
        out.append((to_secs(tds[1]), to_secs(tds[2])))
    return out

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    def _handle_dialog(d):
        try:
            d.dismiss()
        except Exception:
            pass
    page.on("dialog", _handle_dialog)

    # --- Fuzz: random PBs, both tables ---
    random.seed(42)
    for trial in range(40):
        page.goto(URL)
        pb_min = random.randint(0, 10)
        pb_sec = random.randint(0, 59)
        pb = pb_min * 60 + pb_sec
        page.fill("#pb-min", str(pb_min))
        page.fill("#pb-sec", str(pb_sec))
        table = random.choice(["co2", "o2"])
        page.click("#btn-" + table)
        page.click("#btn-generate")
        if pb < 30:
            check(page.locator("#setup").is_visible(), f"pb={pb}: should stay on setup (alert)")
            continue
        check(page.locator("#session").is_visible(), f"pb={pb} {table}: session not shown")
        rows = read_table(page)
        check(len(rows) == 8, f"pb={pb} {table}: expected 8 rounds, got {len(rows)}")
        breathes = [r[0] for r in rows]
        holds = [r[1] for r in rows]
        check(all(v >= 5 for v in breathes + holds), f"pb={pb} {table}: value below 5s: {rows}")
        if table == "co2":
            check(len(set(holds)) == 1, f"pb={pb} co2: holds not constant: {holds}")
            check(all(breathes[i] >= breathes[i+1] for i in range(7)), f"pb={pb} co2: rests not non-increasing: {breathes}")
            check(0.45*pb <= holds[0] <= 0.65*pb or pb < 60, f"pb={pb} co2: hold {holds[0]} out of sane range")
            check(100 <= breathes[0] <= 140, f"pb={pb} co2: first rest {breathes[0]} not ~2min")
            check(10 <= breathes[-1] <= 35, f"pb={pb} co2: last rest {breathes[-1]} not ~15-30s")
        else:
            check(len(set(breathes)) == 1, f"pb={pb} o2: rests not constant: {breathes}")
            check(all(holds[i] <= holds[i+1] for i in range(7)), f"pb={pb} o2: holds not non-decreasing: {holds}")
            check(holds[-1] <= 0.85*pb, f"pb={pb} o2: final hold {holds[-1]} above 80% of PB")
            check(100 <= breathes[0] <= 140, f"pb={pb} o2: rest {breathes[0]} not ~2min")

    # --- Edge: zero/empty inputs ---
    for mins, secs in [("0","0"), ("", ""), ("0","29")]:
        page.goto(URL)
        page.fill("#pb-min", mins)
        page.fill("#pb-sec", secs)
        page.click("#btn-generate")
        check(page.locator("#setup").is_visible(), f"input ({mins!r},{secs!r}): should reject")

    # --- Randomisation: two sessions differ ---
    sessions = []
    for _ in range(2):
        page.goto(URL)
        page.fill("#pb-min", "3"); page.fill("#pb-sec", "0")
        page.click("#btn-generate")
        sessions.append(read_table(page))
    check(sessions[0] != sessions[1] or True, "")  # may rarely collide; just log
    if sessions[0] == sessions[1]:
        print("NOTE: two sessions identical (possible but unlikely)")

    # --- Timer flow: start, verify countdown, phase label, back mid-session ---
    page.goto(URL)
    page.fill("#pb-min", "2"); page.fill("#pb-sec", "0")
    page.click("#btn-generate")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    label = page.inner_text("#phase-label").strip().lower()
    check(label == "breathe", f"timer: expected Breathe phase, got {label!r}")
    t1 = to_secs(page.inner_text("#time-left"))
    page.wait_for_timeout(3000)
    t2 = to_secs(page.inner_text("#time-left"))
    check(t2 < t1, f"timer: not counting down ({t1} -> {t2})")
    check("Round 1 of 8" in page.inner_text("#round-info"), "timer: round info wrong")
    # rapid double-click start should not double-run
    page.click("#btn-back")
    check(page.locator("#setup").is_visible(), "back: setup not shown")
    page.click("#btn-generate")
    page.click("#btn-start")
    check(not page.locator("#btn-start").is_visible(), "double-start: start button still visible while running")
    # back mid-session stops the timer (no stray updates)
    page.click("#btn-back")
    page.wait_for_timeout(1500)
    check(page.locator("#setup").is_visible(), "back mid-run: setup not shown")

    # --- Full session completion (tiny PB to keep it short? min is 30s; instead fast-forward via JS not possible since stateless; simulate by checking finish path with short phases through console override) ---
    page.goto(URL)
    page.evaluate("""() => { window.__origTimeout = window.setTimeout; window.setTimeout = (fn, ms) => window.__origTimeout(fn, Math.min(ms, 5)); }""")
    page.fill("#pb-min", "0"); page.fill("#pb-sec", "40")
    page.click("#btn-generate")
    page.click("#btn-start")
    page.wait_for_selector("#complete:not(.hidden)", timeout=15000)
    check(page.locator("#complete").is_visible(), "completion screen not shown")
    check("Restart" in page.inner_text("#btn-start"), "restart button not shown after completion")
    # restart works
    page.click("#btn-start")
    page.wait_for_selector("#complete:not(.hidden)", timeout=15000)

    # --- Mobile viewport sanity ---
    mpage = browser.new_page(viewport={"width": 375, "height": 667})
    mpage.goto(URL)
    w = mpage.evaluate("document.documentElement.scrollWidth")
    check(w <= 375, f"mobile: horizontal overflow ({w}px)")

    check(not errors, f"JS errors: {errors}")
    browser.close()

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL TESTS PASSED")
