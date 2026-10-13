# Сценарий репорта на Chainabuse

Сайт: https://www.chainabuse.com → **Report Scam**. Форма на английском, поэтому готовые
ответы тоже на английском: копируйте блоки как есть. Порядок полей на сайте может
немного отличаться, ориентируйтесь по названиям.

`[[ ... ]]` — подставить своё. Без этих данных репорт слабее, но отправить можно.

> ⚠️ **Текст репорта публичный.** Не пишите туда свой адрес кошелька, имя, телефон
> и налоговые подробности. Свои адреса и хэши вписывайте только в поля «Transaction hash»
> и в приватные поля, если сайт их предлагает (email для связи виден только
> Chainabuse).

---

## Шаг 1. Category / Scam type

**Выбрать:** `Other Hack` (или `Hack` / `Wallet drainer` / `Seed phrase compromise`, если
такой пункт есть).

Почему: seed-фраза была скомпрометирована, украдена нативная монета в нескольких сетях.
Это взлом, а не обман с инвестициями. Если позже выяснится, что seed вы вводили на
сайте «claim airdrop» или «wallet sync», меняйте категорию на `Phishing`.

## Шаг 2. Scammer addresses (адреса хакера)

Добавить каждый адрес отдельно, сеть указать **Ethereum (EVM)**. Если можно выбрать
несколько сетей, отметьте также BNB Chain, Optimism, Avalanche.

| # | Адрес | Добавлять? |
|---|---|---|
| 1 | `0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF` | **Да, главный** |
| 2 | `0xb68db755734bA145982aEe57134D9c2a6cF4D200` | Да. Связан: оплатил газ и получал средства обратно |
| 3 | `0xF2397C5274A1B2e20F7d1104e2Be6918665c0955` | Да. Получил 61K USDT |
| 4 | `0xF04CC55ABeD46E82BC3b326480Cda57182D0B2DB` | Да. Получил 26.28K USDT |
| 5 | `0x740d2edD…` (получил 45K USDC) | Только после копирования полного адреса из Arkham |

`0x655e7B3E…` **не добавлять**: это может быть другая жертва.

## Шаг 3. Domain / Website

Оставить пустым. Если вспомните сайт, на котором вводили seed или подключали кошелёк
перед кражей, впишите его: это очень ценная информация.

## Шаг 4. Description (публичное описание) — скопировать целиком

```
Wallet compromise / theft. My private key / seed phrase was compromised and my wallets
were drained. On Oct 2, 2026 at 11:52 UTC, 8.582192 ETH (~$21.5K) was sent from my
address to 0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF in a plain transfer signed with
my key (tx 0x0156f8af4b156174bc5fe492ecc33fe254857494a1a907469cb436011747c6f3).
Approx. 13,500 OP on Optimism was taken afterwards.

The stolen funds were consolidated at 0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF,
which appears to be a collector address for multiple victims: according to Arkham,
roughly $259K was deposited from it to exchanges between Oct 1 and Oct 10, 2026
(ChangeNOW ~$258K, KuCoin ~$895), with no withdrawals back from exchanges.
The address is active on Ethereum, BNB Chain, Optimism and Avalanche.

Large outgoing transfers observed:
- 61,000 USDT  -> 0xF2397C5274A1B2e20F7d1104e2Be6918665c0955
- 45,000 USDC  -> 0x740d2edD... (see Arkham)
- 26,280 USDT  -> 0xF04CC55ABeD46E82BC3b326480Cda57182D0B2DB
- 1.73 ETH     -> ChangeNOW deposit address

Linked address 0xb68db755734bA145982aEe57134D9c2a6cF4D200 funded gas for the main
address and received BNB/ETH/USDT back, likely controlled by the same actor.

If you were drained to any of these addresses, please add your report so the cases
can be linked. Exchanges (ChangeNOW, KuCoin) and stablecoin issuers (Tether, Circle):
please review the deposits and balances above. A report is being filed with FBI IC3.
```

Последнюю фразу про IC3 оставляйте, только если заявление уже подано или будет подано
в ближайшие дни.

## Шаг 5. Losses (ущерб): две строки

**Строка 1 — ETH (подтверждено):**

| Поле | Ответ |
|---|---|
| Amount | `8.582192` |
| Token / Asset | `ETH` |
| Chain | `[[Arbitrum — проверить домен эксплорера: arbiscan.io = Arbitrum]]` |
| USD value | `21473` |

**Строка 2 — OP:**

| Поле | Ответ |
|---|---|
| Amount | `13500` |
| Token / Asset | `OP` |
| Chain | `Optimism` |
| USD value (если спросят) | `[[цена OP на дату кражи × 13 500]]`. Смотреть на CoinGecko → OP → Historical data |

## Шаг 6. Transaction hashes

ETH (готово):
`0x0156f8af4b156174bc5fe492ecc33fe254857494a1a907469cb436011747c6f3`

OP: `[[хэш транзакции, которой OP ушли с вашего адреса]]`

Где взять: optimistic.etherscan.io → вставить **свой** адрес → вкладка **Token Transfers**
→ найти исходящий перевод OP на дату кражи → скопировать Txn Hash (начинается с `0x`,
66 символов).

Хэш — главное доказательство. Если есть возможность, добавьте его.

## Шаг 7. Evidence (файлы)

Прикрепить:
1. Скриншот Arkham по главному адресу (тот, что вы уже сделали).
2. Скриншот страницы транзакции кражи на Etherscan.
3. **Не прикладывать** скриншоты, на которых видны seed, балансы других ваших кошельков или личные данные.

## Шаг 8. Contact / Scammer info

- **Your email:** можно указать. Обычно он не публикуется, его видят Chainabuse и правоохранители.
- **Scammer name / email / phone / social:** оставить пустыми. О хакере вы ничего не знаете,
  а выдуманное только вредит репорту.
- **Did you report to law enforcement?** `Yes, FBI IC3` (если подали) и номер заявления.

## После отправки

- [ ] Сохранить ссылку на репорт в `case/addresses.csv` (колонка notes главного адреса).
- [ ] Раз в неделю заглядывать на страницу адреса на Chainabuse: появятся ли другие жертвы.
  Это бесплатный способ узнать масштаб операции.
- [ ] На Etherscan на странице адреса: **More → Report/Flag Address**, тот же текст коротко.
