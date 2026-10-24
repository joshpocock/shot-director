#!/usr/bin/env python3
"""
tally.py: a running credits ledger for AI video attempts.

Credit prices change, so nothing here is hard-coded. Read the number on the
Generate button before every click and log what it said.

Examples:
  python tally.py add --attempt 1 --mode frames --duration 28 --quality 720p --credits 42 --note "first pass"
  python tally.py mark --attempt 1 --usable no
  python tally.py list
  python tally.py summary --dollars-per-credit 0.02

The ledger is a plain CSV (default: credits-ledger.csv in the current folder,
or set --ledger). Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

PROG = "tally.py"
FIELDS = ["date", "attempt", "mode", "duration_s", "quality", "credits", "usable", "note"]


def die(msg: str, code: int = 2) -> None:
    sys.stderr.write(f"{PROG}: error: {msg}\n")
    sys.exit(code)


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                return []
            missing = [f for f in FIELDS if f not in reader.fieldnames]
            if missing:
                die(f"{path} is not a tally ledger (missing columns: {', '.join(missing)})")
            return [dict(r) for r in reader]
    except OSError as exc:
        die(f"could not read {path}: {exc}")
    return []


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    tmp.replace(path)


def num(txt: str, field: str) -> float:
    try:
        return float(txt)
    except (TypeError, ValueError):
        die(f"bad number in column '{field}': {txt!r}")
    return 0.0


def usable_flag(txt: str | None) -> str:
    t = (txt or "").strip().lower()
    if t in ("y", "yes", "true", "1"):
        return "yes"
    if t in ("n", "no", "false", "0"):
        return "no"
    if t in ("", "?", "unknown"):
        return ""
    die(f"--usable must be yes or no, not {txt!r}")
    return ""


def cmd_add(a) -> None:
    if a.duration <= 0:
        die("--duration must be positive (seconds)")
    if a.credits < 0:
        die("--credits cannot be negative")
    rows = read_rows(a.ledger)
    rows.append({
        "date": a.date or date.today().isoformat(),
        "attempt": str(a.attempt),
        "mode": a.mode.strip().lower(),
        "duration_s": f"{a.duration:g}",
        "quality": a.quality,
        "credits": f"{a.credits:g}",
        "usable": usable_flag(a.usable),
        "note": a.note or "",
    })
    write_rows(a.ledger, rows)
    total = sum(num(r["credits"], "credits") for r in rows)
    print(f"Logged attempt {a.attempt} ({a.mode}, {a.duration:g} s, {a.quality}, {a.credits:g} credits). "
          f"Running total: {total:g} credits in {len(rows)} rows. Ledger: {a.ledger}")


def cmd_mark(a) -> None:
    rows = read_rows(a.ledger)
    hit = [r for r in rows if r["attempt"] == str(a.attempt) and (a.mode is None or r["mode"] == a.mode.lower())]
    if not hit:
        die(f"no row for attempt {a.attempt} in {a.ledger}")
    for r in hit:
        r["usable"] = usable_flag(a.usable)
        if a.note:
            r["note"] = (r["note"] + "; " if r["note"] else "") + a.note
    write_rows(a.ledger, rows)
    print(f"Marked {len(hit)} row(s) for attempt {a.attempt} as usable={usable_flag(a.usable) or 'unknown'}.")


def cmd_list(a) -> None:
    rows = read_rows(a.ledger)
    if not rows:
        print(f"No entries yet in {a.ledger}.")
        return
    head = ["#", "date", "attempt", "mode", "dur", "quality", "credits", "usable", "note"]
    table = [[str(i + 1), r["date"], r["attempt"], r["mode"], r["duration_s"], r["quality"], r["credits"],
              r["usable"] or "?", r["note"]] for i, r in enumerate(rows)]
    widths = [max(len(x) for x in col) for col in zip(head, *table)]
    widths[-1] = min(widths[-1], 60)
    print("  ".join(h.ljust(w) for h, w in zip(head, widths)))
    for row in table:
        row[-1] = row[-1][:60]
        print("  ".join(c.ljust(w) for c, w in zip(row, widths)))


def cmd_summary(a) -> None:
    rows = read_rows(a.ledger)
    if not rows:
        print(f"No entries yet in {a.ledger}.")
        return
    credits = sum(num(r["credits"], "credits") for r in rows)
    secs = sum(num(r["duration_s"], "duration_s") for r in rows)
    usable = [r for r in rows if r["usable"] == "yes"]
    unknown = [r for r in rows if r["usable"] == ""]
    usable_secs = sum(num(r["duration_s"], "duration_s") for r in usable)
    print(f"Ledger: {a.ledger}")
    print(f"Attempts logged: {len(rows)} ({len(usable)} usable, {len(rows) - len(usable) - len(unknown)} not usable, "
          f"{len(unknown)} not marked)")
    print(f"Credits spent: {credits:g}")
    print(f"Seconds generated: {secs:g} (usable: {usable_secs:g})")
    if usable_secs:
        print(f"Credits per usable second: {credits / usable_secs:.2f} (all spend, including failed attempts)")
    else:
        print("Credits per usable second: n/a (no attempt marked usable yet; use: tally.py mark --attempt N --usable yes)")
    if a.dollars_per_credit is not None:
        dollars = credits * a.dollars_per_credit
        line = f"Dollar total: ${dollars:,.2f} at ${a.dollars_per_credit:g} per credit"
        if usable_secs:
            line += f" (${dollars / usable_secs:,.2f} per usable second)"
        print(line)
    by_mode: dict[str, list[float]] = {}
    for r in rows:
        m = by_mode.setdefault(r["mode"] or "?", [0, 0.0, 0.0])
        m[0] += 1
        m[1] += num(r["credits"], "credits")
        m[2] += num(r["duration_s"], "duration_s")
    print("By mode:")
    for mode, (count, c, s) in sorted(by_mode.items()):
        print(f"  {mode}: {count} attempt(s), {c:g} credits, {s:g} s")


def main() -> None:
    ap = argparse.ArgumentParser(prog=PROG, description="Running credits ledger for AI video attempts (CSV).")
    ap.add_argument("--ledger", type=Path, default=Path("credits-ledger.csv"),
                    help="CSV ledger path (default: credits-ledger.csv in the current folder)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add", help="log one generation")
    p.add_argument("--attempt", required=True, type=int, help="attempt number")
    p.add_argument("--mode", required=True, help="frames, references, edit, image, or any label")
    p.add_argument("--duration", required=True, type=float, help="seconds generated")
    p.add_argument("--quality", required=True, help="e.g. 720p or 1080p")
    p.add_argument("--credits", required=True, type=float, help="credits charged (read the Generate button)")
    p.add_argument("--note", default="", help="free text")
    p.add_argument("--usable", default="", help="yes or no (can be set later with mark)")
    p.add_argument("--date", default="", help="YYYY-MM-DD (default: today)")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("mark", help="set usable yes/no on an attempt after grading")
    p.add_argument("--attempt", required=True, type=int)
    p.add_argument("--usable", required=True, help="yes or no")
    p.add_argument("--mode", default=None, help="only rows with this mode")
    p.add_argument("--note", default="", help="text to append to the note")
    p.set_defaults(func=cmd_mark)

    p = sub.add_parser("list", help="print every row")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("summary", help="totals, credits per usable second, dollar total")
    p.add_argument("--dollars-per-credit", type=float, default=None, help="your plan's price per credit")
    p.set_defaults(func=cmd_summary)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
