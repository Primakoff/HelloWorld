# After Dark: 3D-графика для ивента

Сцена для Rebirth.Ukraine × 135 Club, «After Dark», Immersive Halloween Experience,
30 октября, 19:00–01:00, Ukrainian National Home, 140 2nd Ave, NYC.

## Что здесь

| Файл | Что это |
|---|---|
| `index.html` | Живая 3D-сцена в реальном времени (Three.js / WebGL). Открывается в любом браузере. |
| `render.mjs` | Рендер кадров в 4K через headless Chromium и сборка видео. |
| `out/` | Готовые файлы: 4K-видео 16:9, 4K-видео 9:16 для Stories/Reels, стоп-кадры без текста. |

Сцена: полукруг фигур в рваных льняных балахонах и гипсовых масках (солнце, тернии,
полумесяц, затмение, звезда, птичий клюв), одна фигура на коленях тянется к свечам.
Сверху бьёт прожектор, в воздухе пыль и пепел, на заднем плане бледный полумесяц.
Цвет: сепия и монохром как на постере, красный сохраняется только в контровом свете.
Петля длится 10 секунд и замыкается без шва.

## Перерендер

```bash
npm i three@0.158.0 playwright
THREE_JS=node_modules/three/build/three.min.js node render.mjs out/h 3840 2160 24 1 frames
ffmpeg -framerate 24 -i out/h/f_%04d.png -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p after-dark-4k.mp4
```

Аргументы: `<папка> <ширина> <высота> <fps> <текст 1|0> <frames | still:t1,t2>`.

## Промпты для AI-видеомоделей (Veo 3, Sora, Runway Gen-4, Kling 2)

Используй стоп-кадр из `out/clean*` как стартовый кадр (image-to-video), чтобы сохранить стиль.

**Основной (16:9, 8–10 с):**
> Cinematic slow dolly shot in a pitch-black theatre. A ritual circle of dancers in torn,
> ash-grey linen robes and white plaster masks: a radiant sun crown with long spikes, a
> crescent moon, a five-point star, a beaked bird mask, a crown of thorns. One dancer kneels
> in front, reaching toward a ring of small candles on a wet black floor. A single hard
> spotlight from above cuts through drifting dust and haze. Monochrome sepia grade, deep
> crushed blacks, subtle red rim light, 35mm film grain, shallow depth of field, slow
> hypnotic movement, Ukrainian folk-horror mood. 4K, 24 fps.

**Вертикальный (9:16, для Reels/Stories):**
> Vertical 9:16. Low-angle shot rising slowly toward a dancer in a white plaster sun mask
> with radiating spikes, arms raised, torn linen sleeves moving in still air, single
> overhead spotlight, dust particles, black void background, faint giant crescent moon in
> haze, sepia monochrome with a thin red edge light, film grain, 4K.

**Негатив (если модель поддерживает):** cartoon, bright colors, gore, blood, modern clothing,
smiling faces, text, watermark.
