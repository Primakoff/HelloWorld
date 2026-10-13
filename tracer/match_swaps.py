#!/usr/bin/env python3
"""Find candidate payouts of an instant-swap service (ChangeNOW, FixedFloat, ...)
for deposits the actor made into it.

On-chain, the trail ends at the service: all customers' coins are pooled. But an
instant swap pays out minutes after the deposit, for about the same USD value
minus a fee. So for each deposit we list the service's outgoing transfers inside
a time window with a close USD value. These are CANDIDATES, not proof: only the
service's own records (order id) confirm a match.

Usage:
    python3 match_swaps.py --deposits hacker.csv --deposit-label changenow \
        --payouts changenow_hot_0x3f3.csv changenow_hot_0xf9a.csv \
        --target 0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import load, short, usd  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--deposits", nargs="+", required=True, help="actor's transfer exports")
    p.add_argument("--target", action="append", required=True, help="actor address (repeatable)")
    p.add_argument("--deposit-label", default="changenow",
                   help="substring of the receiving label that marks a deposit into the service")
    p.add_argument("--payouts", nargs="+", required=True, help="exports of the service's hot wallets")
    p.add_argument("--min-delay", type=float, default=1, help="minutes")
    p.add_argument("--max-delay", type=float, default=60, help="minutes")
    p.add_argument("--fee-max", type=float, default=0.05, help="max share the payout may be below the deposit")
    p.add_argument("--over-max", type=float, default=0.01, help="max share the payout may be above the deposit")
    p.add_argument("--top", type=int, default=5, help="candidates per deposit")
    p.add_argument("--out", default="swap_candidates.md")
    a = p.parse_args()

    actor = {t.lower() for t in a.target}
    needle = a.deposit_label.lower()
    deposits = [r for r in load(a.deposits)
                if r["from"] in actor and needle in r["to_label"].lower() and r["time"] and r["usd"]]
    deposit_addrs = {d["to"] for d in deposits}
    # Payouts: leaving the service, not going back into its own deposit addresses or to the actor.
    payouts = [r for r in load(a.payouts)
               if r["time"] and r["usd"] and r["to"] not in deposit_addrs
               and needle not in r["to_label"].lower()]

    lines = ["# Кандидаты на выплаты ChangeNOW (вероятностное сопоставление)\n",
             f"Окно: {a.min_delay:g}–{a.max_delay:g} мин после депозита; выплата от "
             f"−{a.fee_max:.0%} до +{a.over_max:.0%} от суммы депозита в USD.\n",
             "**Это кандидаты, а не доказательства.** Подтвердить может только ChangeNOW "
             "по номеру заказа (через запрос правоохранителей).\n"]
    if not deposits:
        lines.append(f"Депозитов с меткой «{a.deposit_label}» от адресов {sorted(actor)} не найдено.")
    for d in sorted(deposits, key=lambda r: r["time"]):
        lines.append(f"\n## {d['time']:%Y-%m-%d %H:%M} UTC · {d['amount']} {d['token']} ({usd(d['usd'])}) "
                     f"→ {d['to_label']} `{short(d['to'])}`")
        if d["hash"]:
            lines.append(f"tx `{d['hash']}`\n")
        scored = []
        for r in payouts:
            delay = (r["time"] - d["time"]).total_seconds() / 60
            diff = (r["usd"] - d["usd"]) / d["usd"]
            if a.min_delay <= delay <= a.max_delay and -a.fee_max <= diff <= a.over_max:
                # Closer in value matters more than closer in time; typical fee is ~0.5–2%.
                score = abs(diff + 0.01) * 10 + delay / a.max_delay
                scored.append((score, delay, diff, r))
        if not scored:
            lines.append("Кандидатов нет: расширьте окно или выгрузите выплаты в другой сети (BTC, TRON, …).")
            continue
        lines.append("| Задержка | Δ USD | Выплата | Кому | Метка | Сеть | tx |\n|---|---|---|---|---|---|---|")
        for score, delay, diff, r in sorted(scored, key=lambda s: s[0])[:a.top]:
            lines.append(f"| {delay:.0f} мин | {diff:+.1%} | {r['amount']} {r['token']} ({usd(r['usd'])}) | "
                         f"`{r['to']}` | {r['to_label']} | {r['chain']} | `{short(r['hash'])}` |")
        if len(scored) > a.top:
            lines.append(f"\n…и ещё {len(scored) - a.top}. Чем больше кандидатов, тем слабее каждый.")

    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(deposits)} deposits, {len(payouts)} payouts -> {a.out}")


if __name__ == "__main__":
    main()
