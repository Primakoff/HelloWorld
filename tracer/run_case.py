#!/usr/bin/env python3
"""Whole-case pipeline: download every full address in case/addresses.csv from the
Etherscan v2 API, then write one report for the hacker cluster and one report per
address, so each hypothesis (victim? sweeper? operator?) can be checked.

Needs ETHERSCAN_API_KEY and network access to api.etherscan.io (see README).

Usage:
    python3 tracer/run_case.py                 # fetch + reports
    python3 tracer/run_case.py --skip-fetch    # rebuild reports from case/data/
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze  # noqa: E402
from fetch_etherscan import CHAINS, fetch, write  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")
# Rough prices for rows without USD; ETH from the theft tx ($21,473 / 8.582 ETH on Oct 2).
DEFAULT_PRICES = ["ETH=2500", "BNB=740", "AVAX=9.4", "POL=0.093", "OP=0.13"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chains", nargs="+", default=["eth", "arb", "op", "bsc", "base", "avax", "polygon"],
                   choices=CHAINS)
    p.add_argument("--price", action="append", default=[], metavar="SYM=USD")
    p.add_argument("--min-usd", type=float, default=50.0)
    p.add_argument("--skip-fetch", action="store_true")
    a = p.parse_args()

    prices = {k.upper(): float(v) for k, v in (s.split("=", 1) for s in DEFAULT_PRICES + a.price)}
    with open(ROOT / "case" / "addresses.csv", encoding="utf-8") as f:
        entries = [r for r in csv.DictReader(f) if ADDRESS.match(r["address"].strip())]
    data, reports = ROOT / "case" / "data", ROOT / "case" / "reports"
    data.mkdir(exist_ok=True)
    reports.mkdir(exist_ok=True)

    if not a.skip_fetch:
        key = os.environ.get("ETHERSCAN_API_KEY") or sys.exit("set ETHERSCAN_API_KEY (see README)")
        for e in entries:
            print(f"fetch {e['role']:<18} {e['address']}")
            write(data / f"{e['address'].lower()}.csv", fetch(key, e["address"], a.chains))

    files = [data / f"{e['address'].lower()}.csv" for e in entries]
    files = [f for f in files if f.exists()]
    if not files:
        sys.exit("no data in case/data/: run without --skip-fetch first")

    cluster = {e["address"].lower() for e in entries if e["role"].startswith("hacker")}
    rows = analyze.load(files, prices)
    text, _, cps = analyze.report(rows, cluster, a.min_usd)
    (reports / "cluster.md").write_text(text + "\n", encoding="utf-8")
    analyze.write_next_hops(reports / "next_hops.csv", cps, a.min_usd)
    print(f"cluster ({len(cluster)} addresses) -> case/reports/cluster.md")

    for e in entries:
        own = data / f"{e['address'].lower()}.csv"
        if not own.exists():
            continue
        name = f"{e['role'].rstrip('?')}_{e['address'][:10].lower()}.md"
        text, _, _ = analyze.report(analyze.load([own], prices), {e["address"].lower()}, a.min_usd)
        (reports / name).write_text(f"> Роль в деле: **{e['role']}** ({e['status']}). {e['notes']}\n\n"
                                    + text + "\n", encoding="utf-8")
        print(f"  {e['role']:<18} -> case/reports/{name}")


if __name__ == "__main__":
    main()
