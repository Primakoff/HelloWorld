# After Dark: промпты для ChatGPT и Gemini

Промпты на английском: так модели понимают их точнее. Прикладывайте к запросу постер
(картинку с фигурами), чтобы модель держала стиль костюмов.

Порядок работы:
1. Сначала сгенерируйте **фото** в высоком разрешении (шаг 1).
2. Потом оживите это фото в **видео** (шаг 2): Gemini → Veo, ChatGPT → Sora.
3. Готовые ролики пришлите мне: склею клип, сделаю 4K, звук и титры.

---

## Шаг 1. Фото существ в костюмах

Где: ChatGPT (генерация изображений) или Gemini (Nano Banana / Imagen).
Приложите постер и напишите:

### Групповое фото, 16:9

```
Using the attached poster as a style and costume reference, create a new high-resolution
photograph (16:9, photorealistic, shot on a medium-format camera) of a theatre ritual:
eight dancers dressed as mythical creatures, half human, half celestial spirit.
Costumes: long torn ash-grey linen rags and fringe hanging in strips, bare arms and
shoulders dusted with grey ash. Masks are cracked white plaster: a radiant sun with long
sharp rays, a crescent moon worn sideways over the face, a five-point star, a long bird
beak, a crown of thin thorns and branches. Faces under the masks are pale and still.
Composition: a pyramid of bodies on a black stage, some standing with arms raised, some
crouching, one in front on the floor reaching toward the camera.
Light: one hard spotlight from top right, drifting smoke, deep black background,
wet reflective black floor. Grade: desaturated sepia and charcoal grey, crushed blacks,
very subtle red accent. Fine film grain. No text, no logos, no watermark.
```

### Вертикальное фото, 9:16 (для Reels и Stories)

```
Same costumes, light and grade as the attached poster. Vertical 9:16 photo, low angle:
a single dancer in a cracked white plaster sun mask with long sharp rays, torn grey linen
rags, arms raised high, fingers bent like claws. Behind, in smoke, two more figures in
crescent-moon and star masks. One hard top light, black void, wet floor reflection,
sepia-grey grade, film grain. Photorealistic, no text.
```

### Портреты отдельных масок (для склеек в клипе)

```
Close-up portrait, 16:9, of a dancer wearing a cracked white plaster [SUN / CRESCENT MOON /
FIVE-POINT STAR / BIRD BEAK / CROWN OF THORNS] mask, torn grey linen rags around the
shoulders, ash on the skin, eyes barely visible in the dark eye holes, hard light from
top right, smoke, black background, sepia-grey grade, film grain, photorealistic, no text.
```

Подставляйте в скобки по одной маске, получится серия из пяти портретов.

---

## Шаг 2. Видео из фото

Где: Gemini → Veo (режим «видео из изображения»), ChatGPT → Sora.
Загрузите фото из шага 1 как стартовый кадр. Одна сцена — один запрос, 8 секунд.

Движения взяты из вашей репетиции.

### Сцена 1. Пробуждение

```
Very slow push-in. The masked creatures stand frozen in the dark, then one by one lift their
heads and slowly raise their arms overhead; linen rags tremble; the spotlight flickers on.
Keep the costumes, masks and lighting exactly as in the image. Cinematic, 24 fps, film grain.
```

### Сцена 2. Крылья

```
Slow orbit around the group. The creatures spread their arms wide like wings and sway
together in a hypnotic ritual; dust floats in the light beam; giant shadows move on the
wall behind them. Keep costumes and masks identical. Cinematic, film grain.
```

### Сцена 3. Падение и звери

```
Sudden movement: the creatures fold to the floor and crouch like animals, fingers bent like
claws, heads jerking in unnatural stop-motion twitches; deep red light rises from the floor.
Keep costumes and masks identical. Dark, unsettling, cinematic, film grain.
```

### Сцена 4. Выпад

```
Low angle. The creatures explode upward in wide lunges toward the camera, rags flying,
white strobe flashes, then everything cuts to black. Keep costumes and masks identical.
```

### Если сервис даёт только одну генерацию

```
8-second cinematic shot from the attached image. The masked creatures awaken: they raise
their heads and arms slowly, then spread their arms like wings and sway in a ritual, rags
trembling, smoke drifting through one hard top light, a slow push-in toward the dancer in
the sun mask on the floor. Keep costumes, masks and lighting exactly as in the image.
Sepia-grey grade, deep blacks, faint red accent, film grain.
```

---

## Что писать, если модель портит картинку

Добавьте в конец любого промпта:

```
Avoid: cartoon, anime, bright colors, daylight, gore, blood, smiling faces, extra limbs,
distorted hands, text, captions, logos, watermark, modern clothing.
```

- Маски «плывут» или меняются между кадрами: допишите `the masks are rigid plaster objects and never change shape`.
- Слишком светло: допишите `low-key lighting, 80% of the frame is pure black`.
- Слишком быстро и хаотично: допишите `slow, deliberate, ritual movement`.
