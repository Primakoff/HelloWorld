#!/usr/bin/env python3
"""Download native and token transfers for an address from the Etherscan v2 API
into a CSV that analyze.py reads.

Get a free key at https://etherscan.io/myapikey (one key covers all v2 chains,
though the free plan may not include every chain; fall back to an Arkham or
explorer CSV export for those).

Usage:
    ETHERSCAN_API_KEY=... python3 fetch_etherscan.py 0xF889... --chains eth op bsc arb base
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

CHAINS = {"eth": 1, "op": 10, "bsc": 56, "polygon": 137, "base": 8453, "arb": 42161,
          "avax": 43114, "linea": 59144, "scroll": 534352, "zksync": 324}
NATIVE = {"eth": "ETH", "op": "ETH", "bsc": "BNB", "polygon": "POL", "base": "ETH",
          "arb": "ETH", "avax": "AVAX", "linea": "ETH", "scroll": "ETH", "zksync": "ETH"}
API = "https://api.etherscan.io/v2/api"


def call(key, chainid, **params):
    q = urllib.parse.urlencode({"chainid": chainid, "apikey": key, **params})
    for attempt in range(4):
        with urllib.request.urlopen(f"{API}?{q}", timeout=30) as resp:
            data = json.load(resp)
        result = data.get("result")
        if data.get("status") == "1":
            return result
        if isinstance(result, str) and "rate limit" in result.lower():
            time.sleep(2 ** attempt)
            continue
        if data.get("message") == "No transactions found":
            return []
        print(f"  chain {chainid} {params['action']}: {result}", file=sys.stderr)
        return []
    return []


HEADER = ["hash", "from", "to", "token", "amount", "chain", "timestamp"]


def fetch(key, address, chains):
    rows = []
    for name in chains:
        cid = CHAINS[name]
        base = dict(module="account", address=address, startblock=0, endblock=99999999, sort="asc")
        for tx in call(key, cid, action="txlist", **base):
            if int(tx["value"]) == 0 or tx.get("isError") == "1":
                continue
            rows.append([tx["hash"], tx["from"], tx["to"], NATIVE[name],
                         int(tx["value"]) / 1e18, name, tx["timeStamp"]])
        for tx in call(key, cid, action="txlistinternal", **base):
            if int(tx["value"]) == 0 or tx.get("isError") == "1":
                continue
            rows.append([tx["hash"], tx["from"], tx["to"], NATIVE[name],
                         int(tx["value"]) / 1e18, name, tx["timeStamp"]])
        for tx in call(key, cid, action="tokentx", **base):
            dec = int(tx.get("tokenDecimal") or 18)
            rows.append([tx["hash"], tx["from"], tx["to"], tx["tokenSymbol"],
                         int(tx["value"]) / 10 ** dec, name, tx["timeStamp"]])
        print(f"  {address[:10]} {name}: {len(rows)} rows so far")
        time.sleep(0.4)
    return rows


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("address")
    p.add_argument("--chains", nargs="+", default=["eth", "op", "bsc", "arb", "base"], choices=CHAINS)
    p.add_argument("--out")
    a = p.parse_args()
    key = os.environ.get("ETHERSCAN_API_KEY") or sys.exit("set ETHERSCAN_API_KEY")
    out = a.out or f"{a.address.lower()[:10]}.csv"
    write(out, fetch(key, a.address, a.chains))
    print(f"-> {out}  (no USD column: Etherscan does not give historical prices; "
          "Arkham export does)")


if __name__ == "__main__":
    main()
