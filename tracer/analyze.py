#!/usr/bin/env python3
"""On-chain flow analyzer for a theft investigation.

Reads transfer exports (Arkham "Transfers" CSV, Etherscan CSV, or the output of
fetch_etherscan.py) for one or more addresses that belong to the same actor
(the "cluster") and writes a Markdown report plus a list of next hops to trace.

Usage:
    python3 analyze.py --target 0xF889... [--target 0xb68d...] export1.csv [export2.csv ...]
    python3 analyze.py --target 0xF889... --out ../case/report.md exports/*.csv
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Header aliases, compared after lowercasing and dropping non-alphanumerics.
COLUMNS = {
    "hash": ["transactionhash", "txhash", "hash", "txnhash", "transaction"],
    "from": ["fromaddress", "from", "sender"],
    "from_label": ["fromlabel", "fromentity", "fromaddresslabel", "fromname", "fromnametag"],
    "to": ["toaddress", "to", "recipient", "receiver"],
    "to_label": ["tolabel", "toentity", "toaddresslabel", "toname", "tonametag"],
    "token": ["tokensymbol", "token", "symbol", "tokenname", "asset"],
    "amount": ["unitvalue", "amount", "quantity", "tokenvalue", "value", "valuein", "qty"],
    "usd": ["historicalusd", "usd", "valueusd", "usdvalue", "historicalvalueusd", "valueinusd"],
    "chain": ["chain", "network", "blockchain"],
    "time": ["blocktimestamp", "timestamp", "datetime", "datetimeutc", "time", "date", "unixtimestamp"],
}

# Substrings in a label that mark a custodial service: a KYC lead or a swap service.
EXCHANGES = [
    "binance", "coinbase", "kucoin", "okx", "bybit", "kraken", "huobi", "htx", "gate",
    "mexc", "bitget", "bitfinex", "crypto.com", "changenow", "fixedfloat", "simpleswap",
    "sideshift", "stealthex", "exolix", "changelly", "robinhood", "deposit",
]
MIXERS = ["tornado", "railgun", "mixer", "wasabi", "sinbad", "blender"]
BRIDGES = ["bridge", "stargate", "across", "hop protocol", "synapse", "relay", "orbiter",
           "lifi", "li.fi", "jumper", "socket", "wormhole", "thorchain", "layerzero"]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def parse_number(raw):
    """'$26.28K' -> 26280.0, '1,349.5' -> 1349.5, '' -> None."""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace("$", "").replace(" ", "")
    if not s or s in {"-", "—"}:
        return None
    mult = 1.0
    if s[-1:].upper() in "KMB" and len(s) > 1:
        mult = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1].upper()]
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def parse_time(raw):
    if not raw:
        return None
    s = str(raw).strip()
    if s.isdigit():
        n = int(s)
        return datetime.fromtimestamp(n / 1000 if n > 1e12 else n, tz=timezone.utc)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
                "%m/%d/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def map_columns(header):
    normalized = {norm(h): h for h in header}
    mapping = {}
    for key, aliases in COLUMNS.items():
        for alias in aliases:
            if alias in normalized:
                mapping[key] = normalized[alias]
                break
    return mapping


def load(paths):
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            cols = map_columns(reader.fieldnames or [])
            missing = [k for k in ("from", "to") if k not in cols]
            if missing:
                sys.exit(f"{path}: no column for {missing}; headers are {reader.fieldnames}")
            for r in reader:
                get = lambda k: (r.get(cols[k]) or "").strip() if k in cols else ""
                rows.append({
                    "hash": get("hash"),
                    "from": get("from").lower(),
                    "from_label": get("from_label"),
                    "to": get("to").lower(),
                    "to_label": get("to_label"),
                    "token": get("token") or "?",
                    "amount": parse_number(get("amount")),
                    "usd": parse_number(get("usd")),
                    "chain": get("chain") or Path(path).stem,
                    "time": parse_time(get("time")),
                })
    # The same transfer can appear in exports of two cluster addresses.
    seen, unique = set(), []
    for r in rows:
        key = (r["hash"], r["from"], r["to"], r["token"], r["amount"])
        if r["hash"] and key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique


def classify(label):
    low = (label or "").lower()
    if any(m in low for m in MIXERS):
        return "mixer"
    if any(e in low for e in EXCHANGES):
        return "exchange"
    if any(b in low for b in BRIDGES):
        return "bridge"
    return ""


def short(addr):
    return addr if len(addr) < 14 else f"{addr[:8]}…{addr[-4:]}"


def usd(v):
    return f"${v:,.2f}" if v is not None else "—"


def analyze(rows, cluster, min_usd):
    inflow, outflow, internal = [], [], []
    for r in rows:
        f_in, t_in = r["from"] in cluster, r["to"] in cluster
        if f_in and t_in:
            internal.append(r)
        elif t_in:
            inflow.append(r)
        elif f_in:
            outflow.append(r)

    cps = defaultdict(lambda: {"label": "", "in": 0.0, "out": 0.0, "n": 0, "first": None,
                               "last": None, "tokens": set(), "chains": set()})
    for direction, items in (("in", inflow), ("out", outflow)):
        for r in items:
            addr = r["from"] if direction == "in" else r["to"]
            label = r["from_label"] if direction == "in" else r["to_label"]
            c = cps[addr]
            c["label"] = c["label"] or label
            c[direction] += r["usd"] or 0
            c["n"] += 1
            c["tokens"].add(r["token"])
            c["chains"].add(r["chain"])
            if r["time"]:
                c["first"] = min(filter(None, [c["first"], r["time"]]))
                c["last"] = max(filter(None, [c["last"], r["time"]]))
    for c in cps.values():
        c["kind"] = classify(c["label"])
    return inflow, outflow, internal, cps


def by_key(items, key):
    agg = defaultdict(lambda: [0.0, 0.0, 0])
    for r in items:
        a = agg[r[key]]
        a[0] += r["amount"] or 0
        a[1] += r["usd"] or 0
        a[2] += 1
    return sorted(agg.items(), key=lambda kv: -kv[1][1])


def report(rows, cluster, min_usd):
    inflow, outflow, internal, cps = analyze(rows, cluster, min_usd)
    total_in = sum(r["usd"] or 0 for r in inflow)
    total_out = sum(r["usd"] or 0 for r in outflow)
    timed = [r["time"] for r in rows if r["time"]]
    out = []
    w = out.append

    w("# Отчёт по потокам средств\n")
    w(f"Кластер ({len(cluster)}): " + ", ".join(f"`{a}`" for a in sorted(cluster)) + "\n")
    w(f"Строк: {len(rows)} · входящих {len(inflow)} · исходящих {len(outflow)} · "
      f"внутри кластера {len(internal)}")
    if timed:
        w(f"Период: {min(timed):%Y-%m-%d %H:%M} — {max(timed):%Y-%m-%d %H:%M} UTC")
    w(f"\n**Пришло: {usd(total_in)} · Ушло: {usd(total_out)}** "
      "(USD по исторической цене, если она есть в выгрузке)\n")

    w("## 1. Финансирование: первые входящие\n")
    w("Первый мелкий перевод нативной монеты обычно оплачивает газ. Его отправитель — "
      "главная ниточка к кошельку, с которого всё началось.\n")
    w("| Время | От | Метка | Сумма | Токен | USD | Сеть |\n|---|---|---|---|---|---|---|")
    for r in sorted((r for r in inflow if r["time"]), key=lambda r: r["time"])[:10]:
        w(f"| {r['time']:%m-%d %H:%M} | `{short(r['from'])}` | {r['from_label'] or ''} | "
          f"{r['amount'] or ''} | {r['token']} | {usd(r['usd'])} | {r['chain']} |")

    for title, items in (("2. Входящие по токенам", inflow), ("3. Исходящие по токенам", outflow)):
        w(f"\n## {title}\n")
        w("| Токен | Кол-во | USD | Переводов |\n|---|---|---|---|")
        for tok, (amt, v, n) in by_key(items, "token"):
            w(f"| {tok} | {amt:,.4f} | {usd(v)} | {n} |")

    w("\n## 4. Сети\n")
    w("| Сеть | Вход USD | Выход USD |\n|---|---|---|")
    chains = {c for c, _ in by_key(inflow, "chain")} | {c for c, _ in by_key(outflow, "chain")}
    for ch in sorted(chains):
        i = sum(r["usd"] or 0 for r in inflow if r["chain"] == ch)
        o = sum(r["usd"] or 0 for r in outflow if r["chain"] == ch)
        w(f"| {ch} | {usd(i)} | {usd(o)} |")

    w("\n## 5. Сервисы: биржи, обменники, мосты, миксеры\n")
    w("Депозит на биржу с KYC — точка, где у правоохранителей появляется личность.\n")
    w("| Тип | Адрес | Метка | Отправлено туда USD | Переводов |\n|---|---|---|---|---|")
    svc = sorted((kv for kv in cps.items() if kv[1]["kind"]), key=lambda kv: -kv[1]["out"])
    for addr, c in svc:
        w(f"| {c['kind']} | `{addr}` | {c['label']} | {usd(c['out'])} | {c['n']} |")
    if not svc:
        w("| — | — | в выгрузке нет меток сервисов | — | — |")

    w("\n## 6. Контрагенты (топ-30 по объёму)\n")
    w("| Адрес | Метка | Вход USD | Выход USD | Tx | Первый | Последний | Сети |\n"
      "|---|---|---|---|---|---|---|---|")
    top = sorted(cps.items(), key=lambda kv: -(kv[1]["in"] + kv[1]["out"]))[:30]
    for addr, c in top:
        two_way = " ⇄" if c["in"] and c["out"] else ""
        w(f"| `{addr}`{two_way} | {c['label']} | {usd(c['in'])} | {usd(c['out'])} | {c['n']} | "
          f"{c['first']:%m-%d %H:%M} | {c['last']:%m-%d %H:%M} | {', '.join(sorted(c['chains']))} |"
          if c["first"] else
          f"| `{addr}`{two_way} | {c['label']} | {usd(c['in'])} | {usd(c['out'])} | {c['n']} | — | — | "
          f"{', '.join(sorted(c['chains']))} |")
    w("\n⇄ — деньги шли в обе стороны. Это сильный признак второго кошелька того же человека: "
      "кандидат в кластер (`--target`).")

    w("\n## 7. Хронология по дням\n")
    w("| День | Вход USD | Выход USD |\n|---|---|---|")
    days = defaultdict(lambda: [0.0, 0.0])
    for r in inflow:
        if r["time"]:
            days[r["time"].date()][0] += r["usd"] or 0
    for r in outflow:
        if r["time"]:
            days[r["time"].date()][1] += r["usd"] or 0
    for d in sorted(days):
        w(f"| {d} | {usd(days[d][0])} | {usd(days[d][1])} |")

    w("\n## 8. Граф (Mermaid — откроется на GitHub)\n")
    w("```mermaid\nflowchart LR")
    w('  T(["Кластер хакера"])')
    for i, (addr, c) in enumerate(top[:15]):
        name = (c["label"] or short(addr)).replace('"', "'")
        node = f'N{i}["{name}"]' if not c["kind"] else f'N{i}[("{name}")]'
        if c["in"] >= min_usd:
            w(f"  {node} -->|{usd(c['in'])}| T")
            node = f"N{i}"
        if c["out"] >= min_usd:
            w(f"  T -->|{usd(c['out'])}| {node}")
    w("```")
    return "\n".join(out), outflow, cps


def write_next_hops(path, cps, min_usd):
    hops = sorted(((a, c) for a, c in cps.items() if c["out"] >= min_usd and c["kind"] != "exchange"),
                  key=lambda kv: -kv[1]["out"])
    with open(path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["address", "label", "received_from_cluster_usd", "tx", "chains", "two_way"])
        for a, c in hops:
            wr.writerow([a, c["label"], round(c["out"], 2), c["n"], " ".join(sorted(c["chains"])),
                         bool(c["in"] and c["out"])])
    return len(hops)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="CSV exports")
    p.add_argument("--target", action="append", required=True, help="cluster address (repeatable)")
    p.add_argument("--out", default="report.md")
    p.add_argument("--hops", default="next_hops.csv")
    p.add_argument("--min-usd", type=float, default=100.0, help="threshold for graph and next hops")
    a = p.parse_args()

    cluster = {t.lower() for t in a.target}
    rows = load(a.files)
    text, _, cps = report(rows, cluster, a.min_usd)
    Path(a.out).write_text(text + "\n", encoding="utf-8")
    n = write_next_hops(a.hops, cps, a.min_usd)
    print(f"{len(rows)} transfers -> {a.out}; {n} next hops -> {a.hops}")


if __name__ == "__main__":
    main()
