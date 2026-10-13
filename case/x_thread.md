# Черновик треда в X (по-английски: в крипто-X так больше охват)

Статус: **ЧЕРНОВИК. Не публиковать, пока все `[[...]]` не заполнены и цифры не перепроверены.**

## Правила публикации

1. **Только факты, которые видны в блокчейне,** и у каждого — ссылка на tx или адрес.
   Никого не называть по имени и не «вычислять» людей без доказательств:
   ошибка = клевета и потеря доверия.
2. **Не публиковать:** остаток на ваших кошельках, новые адреса, налоговые подробности.
   Ваш старый (украденный) адрес показать можно: он уже скомпрометирован.
3. **Не писать «пишите в личку».** Вам будут писать мошенники «по возврату».
   Пусть другие жертвы отвечают публично или репортят на Chainabuse.
4. Картинки: граф Arkham (только вокруг адреса хакера, **не** раскрытый роутер OKX),
   скриншот Exchange Usage, скриншот вашей транзакции кражи.
5. Хэндлы проверить перед отправкой (у компаний бывают фейковые аккаунты).

---

## Тред

**1/**
I got drained. Instead of moving on, I traced where my funds went.

Turns out I'm one of dozens.

0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF received funds from ~[[N]] addresses and pushed $[[TOTAL]]+ out through ChangeNOW and KuCoin in 10 days.

Thread 🧵

**2/**
What happened to me:
On [[DATE]], ~13,500 $OP was drained from my wallet on Optimism.

Tx: [[optimistic.etherscan.io/tx/...]]

[[Attack vector, once confirmed — e.g. "The tx was signed by my own key → seed phrase compromise, not a malicious approval."]]

**3/**
The receiving address is a collector, not a one-off wallet.

Inflows from ~[[N]] different addresses across Ethereum, BNB Chain, Optimism, Avalanche, plus bridge inflows (Bridgers).

[graph image]

**4/**
Cash-out path (Oct 1–10, 2026):
• token swaps via OKX DEX Router and Uniswap
• bridging via deBridge
• [[12+]] separate ChangeNOW deposits — ~$258K
• a KuCoin deposit — ~$895

No funds came back from exchanges. Pure exit.

[Exchange Usage screenshot]

**5/**
Large stablecoin transfers to intermediate addresses:
• 61,000 USDT → 0xF2397C5274A1B2e20F7d1104e2Be6918665c0955
• 45,000 USDC → [[0x740d2… full address]]
• 26,280 USDT → 0xF04CC55ABeD46E82BC3b326480Cda57182D0B2DB

@Tether_to @circle — [[if balances are still there: "funds may still be on these addresses"]]

**6/**
Linked wallet: 0xb68db755734bA145982aEe57134D9c2a6cF4D200
It funded gas for the collector and received BNB/ETH/USDT back — likely the same operator.

**7/**
@ChangeNOW_io @kucoincom — deposit addresses and tx hashes are listed above and in the Chainabuse report: [[link]]
Reported to FBI IC3.

**8/**
Lessons from my own mistake:
[[after the vector is confirmed, e.g.:]]
• a hardware wallet is only cold while its seed never touches an online device
• I typed my seed into my phone "for convenience" — that turned it into a hot wallet
• [[...]]

**9/**
If you were drained to 0xF8895…04bF, reply here or add your report on Chainabuse so the cases can be linked.

Never pay anyone who DMs you promising "recovery." They're the second wave of the same scam.
