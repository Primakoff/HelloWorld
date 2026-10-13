# After Dark: графика для ивента

Rebirth.Ukraine × 135 Club, «After Dark», Immersive Halloween Experience,
30 октября, 19:00–01:00, Ukrainian National Home, 140 2nd Ave, NYC.

## Клип по репетиции (основной результат)

`out/after-dark-clip-4k.mp4`: 3840×2160, 30 fps, около 19 секунд, со звуком.

Сделан из видео с тренировки: танцоров вырезали из зала нейросетью и перенесли на тёмную
ритуальную сцену. На лицах у них гипсовые маски, на головах короны существ.

| Время | Акт | Что происходит |
|---|---|---|
| 0–4.6 с | Тьма | Свет загорается с перебоями, фигуры медленно поднимают руки (замедление 0.55x), сердцебиение |
| 4.6–7.3 с | Крылья | Руки раскрываются в «крылья», появляются призрачные шлейфы |
| 7.3–9.9 с | Падение | Удар, вспышка, фигуры складываются к земле, снизу поднимается красный свет |
| 9.9–13.3 с | Звери | Звериные позы, рывки как в stop-motion, дрожь тел, огромные тени на стене |
| 13.3–15.5 с | Выпад | Резкие выпады, три вспышки на ударах |
| 15.5–19.3 с | Титр | AFTER DARK, дата, адрес |

### Как это сделано

| Шаг | Инструмент |
|---|---|
| Монтаж, замедление с интерполяцией кадров | ffmpeg (`minterpolate`) |
| Вырезание танцоров из зала | MediaPipe Selfie Multiclass Segmenter, по фрагментам кадра с увеличением 2x |
| Положение головы, плеч и глаз каждого танцора | MediaPipe Pose Landmarker (heavy), два прохода, трекинг и сглаживание |
| Увеличение 720p → 4K | Real-ESRGAN (realesr-general-x4v3), сконвертирован в ONNX и запущен через ONNX Runtime |
| Сцена, свет, дым, отражения, тени, маски, короны, грейд, зерно | `clip/render.py` (NumPy + OpenCV), рендер прямо в 4K |
| Звук | `clip/sound.py`, синтез без чужой музыки, поэтому без проблем с авторскими правами |

Исходник снят в 720p, поэтому лица и тела в 4K восстановлены нейросетью. Сцена, свет,
маски и титры рисуются сразу в 4K.

### Перерендер

```bash
pip install mediapipe opencv-python-headless onnx onnxruntime scipy pillow
python3 clip/esrgan_onnx.py realesr-general-x4v3.pth models/realesr-x4v3.onnx
# edit/: кадры планов A–E и shots.txt (см. историю), models/: модели MediaPipe и ONNX, fonts/: Anton, IBM Plex Mono
python3 clip/analyze.py  <work>/edit <work>/models <work>/ana
python3 clip/heads_pass2.py <work>/edit <work>/models <work>/ana
python3 clip/render.py <work> preview 60,180,350     # проверочные кадры
python3 clip/render.py <work> full <work>/frames     # все кадры, можно прерывать и продолжать
python3 clip/sound.py <work>/timeline.json <work>/score.wav
ffmpeg -framerate 30 -i <work>/frames/f_%04d.jpg -i <work>/score.wav -c:v libx264 -crf 14 -preset slow \
  -pix_fmt yuv420p -c:a aac -b:a 320k -shortest out/after-dark-clip-4k.mp4
```

## Живая 3D-сцена (первый вариант)

| Файл | Что это |
|---|---|
| `index.html` | 3D-сцена в реальном времени (Three.js / WebGL), открывается в браузере |
| `render.mjs` | Рендер кадров этой сцены в 4K через headless Chromium |

## Промпты для генеративных видеомоделей (Veo 3, Sora, Runway Gen-4, Kling 2)

Если есть доступ к этим сервисам, возьмите кадр из клипа как стартовый (image-to-video),
чтобы сохранить стиль.

> Dark folk-horror ritual on a black stage. Dancers in black with blank white plaster masks
> and crowns: a spiked sun, a crescent moon, antlers, a five-point star, a crown of thorns.
> They crouch and claw like animals, then rise with arms spread like wings. One hard
> spotlight from above, drifting smoke, giant shadows on the wall behind them, deep red
> underlight from the floor, wet reflective floor, ash-grey grade, 35mm grain, 4K.

**Негатив:** cartoon, bright colors, gore, smiling faces, text, watermark.
