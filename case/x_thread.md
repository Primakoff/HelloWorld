# Тред в X: версия 2 (готов к публикации)

Всё заполнено, пропусков нет. Каждый твит проверен скриптом по правилам подсчёта X
(≤ 280 символов, ссылка = 23). Картинки лежат в `case/img/`.

---

## Этап 0. Подготовка (15 минут, до публикации)

1. **Chainabuse:** отправьте репорт по `case/chainabuse_report.md` (готовые ответы).
2. **FBI IC3:** подайте заявление на [ic3.gov](https://www.ic3.gov). Твит 8 говорит «I'm filing»,
   поэтому достаточно начать подачу.
3. **Картинки:** скачайте 4 файла из `case/img/`:
   | Файл | К какому твиту |
   |---|---|
   | `1_collector_graph.png` | 1 |
   | `2_theft_tx.png` | 2 |
   | `3_first_funder_exchanges.png` | 3 |
   | `4_second_victim.png` | 4 |
4. **Хэндлы:** откройте @zachxbt, @SEAL_Org, @MistTrack_io, @ChangeNOW_io, @kucoincom
   и убедитесь, что это настоящие аккаунты (галочка, много подписчиков, давний аккаунт).

## Этап 1. Публикация

- **Когда:** будний день, 9:00–11:00 по восточному времени (ET). В это время активны и США, и Европа.
- **Как:** в X нажмите «+» в окне создания поста и вставьте все 10 твитов сразу как тред,
  каждый со своей картинкой. Одна публикация лучше, чем добавлять ответы по одному.
- Публикуйте с основного аккаунта, без хэштегов.

## Этап 2. Первые 2 часа

- Закрепите тред в профиле.
- На вопросы отвечайте **публично**, коротко, со ссылкой на транзакцию.
- В личку придут «хакеры», «детективы», «юристы по возврату». Никому не отвечайте,
  ничего не платите, ничего не подключайте.
- Если откликнутся другие жертвы, попросите их **публично** указать адрес и хэш.

## Этап 3. Продолжение

- Когда появится ссылка Chainabuse, добавьте её ответом к своему треду.
- После полного трейсинга (нужен доступ к API, см. README) опубликуйте апдейт
  цитатой своего треда: «Update: …».

---

## Тред

Под каждым твитом — смысл по-русски, чтобы вы знали, что публикуете.

**1/** + `1_collector_graph.png`
```
On Oct 2 my main wallet sent 8.58 ETH (~$21K) to an address I'd never seen. It wasn't me.

A few days later the SafePal wallet on the same iPhone was emptied too.

I spent three weeks tracing it. I'm not the only victim, and the thief has pushed $259K+ through ChangeNOW 🧵
```
> 2 октября с моего кошелька ушло 8.58 ETH на чужой адрес. Это был не я. Через несколько дней
> опустошили и SafePal на том же iPhone. Три недели трейсинга: я не единственная жертва,
> вор вывел $259K+ через ChangeNOW.

**2/** + `2_theft_tx.png`
```
The tx:
https://arbiscan.io/tx/0x0156f8af4b156174bc5fe492ecc33fe254857494a1a907469cb436011747c6f3

No approval, no phishing signature, no contract call. A plain transfer signed with my private key, for 8.582192183030113058 ETH: my exact balance minus gas.

Someone had my key, and a bot used it.
```
> Ни разрешений, ни фишинговых подписей, ни контрактов. Обычный перевод, подписанный моим
> ключом, на сумму «весь баланс минус газ». У кого-то был мой ключ, и им воспользовался бот.

**3/** + `3_first_funder_exchanges.png`
```
It went to 0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF

On Arbitrum, my wallet was its very first funder (per Arkham). On Ethereum it had received 10 ETH from another wallet 47 minutes earlier.

Oct 1–20: ~$258K into ChangeNOW, ~$900 into KuCoin. Nothing came back out.
```
> Деньги ушли на 0xF889. В Arbitrum мой кошелёк — первый, кто его пополнил (по Arkham).
> В Ethereum за 47 минут до меня туда пришло 10 ETH с другого кошелька. С 1 по 20 октября
> ~$258K ушло в ChangeNOW, ~$900 в KuCoin, обратно ничего.

**4/** + `4_second_victim.png`
```
That 10 ETH came from 0x06990583124919da6035B2d2D0121B738aC9BCb2. It looks like a victim, not the thief: normal exchange history, then 10 ETH out.

Around Oct 11 a fresh address sent it 0.001 ETH for gas, then pulled 3.27K XAI. Fund gas, sweep leftovers. Same playbook.
```
> Эти 10 ETH — с кошелька, похожего на жертву, а не на вора: обычная история с биржами,
> потом 10 ETH наружу. Около 11 октября новый адрес прислал ему газ и забрал XAI.
> Схема та же: дать газ, вымести остатки.

**5/**
```
How I think it happened:

Both wallets were on an old iPhone I hadn't updated, still on iOS 18. I'd imported my SafePal hardware wallet seed into the app for convenience, which turned a cold wallet into a hot one.

A friend lost funds the same way. Also an old iPhone on iOS 18.
```
> Как, по-моему, это случилось: оба кошелька на старом необновлённом iPhone с iOS 18.
> Seed от аппаратного SafePal я импортировал в приложение, и холодный кошелёк стал горячим.
> Знакомый потерял средства так же, тоже старый iPhone на iOS 18.

**6/**
```
It fits DarkSword, an iOS 18.4–18.7 exploit kit reported in March by Google GTIG, iVerify and Lookout. It hits iPhones through hacked websites and pulls crypto wallet data within seconds.

Can't prove it was this exact kit. Current iOS is patched.
https://security.lookout.com/blog/darksword
```
> Похоже на DarkSword — набор эксплойтов для iOS 18.4–18.7 (отчёты Google, iVerify, Lookout,
> март). Заражает через взломанные сайты и за секунды забирает данные кошельков. Доказать,
> что это именно он, не могу. В актуальной iOS закрыто.

**7/**
```
What I'd tell anyone:

- Update your iPhone. If it can't run current iOS, don't keep a wallet on it
- Never type a hardware wallet seed into a phone or browser
- After a hack, treat every wallet on that device as burned and move them all at once. I was too slow with my SafePal
```
> Совет всем: обновляйте iPhone, а если он не тянет актуальную iOS, не держите на нём кошелёк.
> Никогда не вводите seed аппаратного кошелька в телефон или браузер. После взлома считайте
> сгоревшими все кошельки на устройстве и переводите сразу все. Я с SafePal не успел.

**8/**
```
If you lost funds to 0xF8895…04bF, reply here so we can connect the cases. I'm filing with FBI IC3 and Chainabuse.

Anyone who DMs you offering "recovery" is a scammer.

@zachxbt @SEAL_Org @MistTrack_io @ChangeNOW_io @kucoincom
```
> Если ваши средства ушли на этот адрес, отпишитесь здесь, свяжем случаи. Подаю в FBI IC3
> и Chainabuse. Кто пишет в личку про «возврат средств» — мошенник.

**9/**
```
Addresses

Victim (me): 0xDFC1AA76eBc7117cCB018dD9833b302153a0F518
Collector: 0xF8895A77af3AD64c56d433DC0Ad0fD8D7D2704bF
Paid the collector's gas, got funds back: 0xb68db755734bA145982aEe57134D9c2a6cF4D200
Likely victim #2: 0x06990583124919da6035B2d2D0121B738aC9BCb2
```
> Список адресов: я; сборщик; адрес, который платил газ сборщику и получал от него деньги;
> вероятная вторая жертва.

**10/**
```
This was my first on-chain investigation. An expensive way to start, but it won't be my last.
```
> Это моё первое ончейн-расследование. Дорогой старт, но не последнее.

---

## Почему текст именно такой

- **Первая строка — история, а не жалоба.** «It wasn't me» цепляет сильнее, чем «I got hacked».
- **Каждое утверждение проверяемо**: ссылка на транзакцию, адрес, источник (Arkham, Lookout).
  За это ZachXBT и SEAL уважают разборы.
- **Честные оговорки** («how I think», «can't prove») не ослабляют тред, а наоборот:
  они показывают, что автор отличает факт от гипотезы.
- **0x0699 назван вероятной жертвой**, а не скамером. Ошибка в обратную сторону — публичное
  обвинение пострадавшего.
- **Сумма $259K+** — только то, что подтверждено Arkham. $1.59M в Visualizer — это объём
  в обе стороны, его в тред не ставим.
- **Теги только в одном твите.** ZachXBT получает тысячи упоминаний. Заметить кейс может за
  новизну: несколько жертв + старый iPhone на iOS 18 + публичный эксплойт.
- **SafePal не отмечен**: их устройство не взломано, seed был введён в телефон.
