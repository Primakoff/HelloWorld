# Тред в X: финальная версия

Стиль: коротко, только проверяемые факты, адреса и ссылки на транзакции. Без хэштегов
и «эмоций ради охвата». Так пишут ZachXBT и SEAL: их читают, потому что каждое
утверждение можно проверить за минуту.

## Проверить перед публикацией (5 минут)

- [ ] **Версия iOS** на старом iPhone: Настройки → Основные → Об этом устройстве.
      DarkSword поражает **iOS 18.4–18.7**. Если версия другая, удалите из твита 5
      фразу про DarkSword и оставьте только «old iPhone on iOS 18.x».
- [ ] **0x0699…** — кошелёк того знакомого, которого тоже взломали? Если да, используйте
      вариант 4A. Если не знаете, чей он, вариант 4B. **Не называйте его кошельком скамера**:
      всё указывает на то, что это вторая жертва (см. README, раздел 1.2).
- [ ] Полный адрес **0x03BEF7E16a75fe…** скопировать из Arkham в твит 4.
- [ ] Ссылка на репорт Chainabuse в твит 7 (сначала отправьте репорт).
- [ ] Главный кошелёк тоже был на этом iPhone? Если нет, поправьте твит 5.
- [ ] Хэндлы: открыть каждый профиль и убедиться, что он настоящий (галочка, подписчики).

**Картинки:**
- твит 1 — граф Arkham вокруг 0xF889 (не раскрытый роутер OKX);
- твит 2 — скриншот arbiscan с транзакцией;
- твит 3 — Exchange Usage (ChangeNOW $258K);
- твит 4 — таблица переводов 0x0699 (10 ETH и XAI + газ).

---

**1/**
```
On Oct 2 my main wallet was drained: 8.58 ETH (~$21K) on Arbitrum. A few days later the SafePal wallet on the same phone got emptied too.

I traced the funds. The address that took them has pushed $259K+ through ChangeNOW, and I'm not the only victim.

What I found 🧵
```

**2/**
```
The theft tx:
https://arbiscan.io/tx/0x0156f8af4b156174bc5fe492ecc33fe254857494a1a907469cb436011747c6f3

A plain ETH transfer signed with my own key. No approval, no contract call. The amount is 8.582192183030113058 ETH, my exact balance minus gas. Looks like a sweeper bot.

So the key itself was stolen.
```

**3/**
```
Receiving address:
0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF

Arkham lists my wallet as its first funder on Arbitrum. 47 minutes earlier it got 10 ETH from another wallet on Ethereum.

Oct 1–20: ~$258K into ChangeNOW, ~$900 into KuCoin. Nothing came back.
```

**4A/** (если 0x0699 — тот самый знакомый)
```
That 10 ETH came from 0x06990583124919da6035B2d2D0121B738aC9BCb2, a friend's wallet. Same story: old iPhone, wallet on the phone.

Around Oct 10, [[0x03BEF…full]] sent it 0.001 ETH for gas and pulled 3.27K XAI right after. Gas in, tokens out.
```

**4B/** (если чей кошелёк, неизвестно)
```
0x06990583124919da6035B2d2D0121B738aC9BCb2 looks like another victim, not the scammer: normal exchange history, then 10 ETH out.

Around Oct 10, [[0x03BEF…full]] sent it 0.001 ETH for gas and pulled 3.27K XAI right after. Gas in, tokens out.
```

**5/**
```
How: both wallets were on an old iPhone on iOS [[18.x]]. I'd imported my SafePal hardware wallet seed into the app. Big mistake.

Can't prove the exploit yet, but DarkSword (GTIG/iVerify/Lookout) hits iOS 18.4–18.7 via hacked sites and grabs wallet data in seconds.
```

**6/**
```
If your iPhone isn't on the latest iOS and has a wallet on it: update now, then move funds to a fresh seed created on a clean device.

And never type a hardware wallet seed into a phone. It stops being cold the moment you do.
```

**7/**
```
If you were drained to 0xF8895…04bF, reply here or add a report on Chainabuse so the cases can be linked: [[link]]

Reported to FBI IC3. Nobody who DMs you offering "recovery" is legit.

@zachxbt @SEAL_Org @MistTrack_io @ChangeNOW_io @kucoincom
```

**8/**
```
This was my first on-chain investigation. Expensive way to start, but I'm not stopping here.
```

---

## Про отметки

- **@zachxbt** получает тысячи упоминаний в день и обычно не берётся за случаи меньше
  нескольких сотен тысяч. Шанс, что он заметит, повышает не тег, а **новизна**: несколько
  жертв, общий паттерн (старый iPhone на iOS 18) и связь с публичным эксплойтом.
  Это у вас есть. Тегайте один раз, в последнем твите, а не в каждом.
- **@SEAL_Org** (Security Alliance) — экстренная помощь при взломах, следят за такими кейсами.
- **@MistTrack_io** (SlowMist) — трекинг украденных средств, иногда помечают адреса.
- **@ChangeNOW_io**, **@kucoincom** — сервисы, через которые выведены деньги: публичное
  упоминание с адресами иногда ускоряет реакцию комплаенса.
- Не тегайте SafePal: их продукт не взломан, seed ввели в телефон вы сами.
  Иначе получится несправедливое обвинение и спор в комментариях.

## После публикации

- Закрепите тред в профиле.
- Отвечайте только публично. В личку придут «хакеры» и «детективы»: всех игнорировать.
- Если откликнутся другие жертвы, внесите их адреса в `addresses.csv` (статус `victim`).
