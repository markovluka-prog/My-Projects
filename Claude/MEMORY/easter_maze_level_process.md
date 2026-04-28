---
name: Easter Maze — процесс создания уровня
description: Правила добавления нового уровня в Easter Maze (index.html, Three.js)
type: project
---

## Структура новой функции buildLevelN()

```javascript
function buildLevel5() {
  specialSignPos = null; // сбросить перед установкой нового

  scene.background = new THREE.Color(0x...);
  scene.fog = new THREE.Fog(0x..., near, far); // или scene.fog.color/near/far

  // 1. Пол — в переменную floor (удаляется вручную в rebuildWorld)
  floor = new THREE.Mesh(new THREE.PlaneGeometry(...), makeMaterial(...));
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.02; // чуть ниже 0 чтобы не было z-fighting с объектами на y=0
  scene.add(floor);

  // 2. Свет — ОБЯЗАТЕЛЬНО в sceneDecor (иначе накапливается между уровнями!)
  const light = new THREE.DirectionalLight(0xffffff, 1.0);
  light.position.set(20, 40, 20);
  scene.add(light);
  sceneDecor.push(light); // ← КРИТИЧНО

  const amb = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(amb);
  sceneDecor.push(amb); // ← КРИТИЧНО

  // 3. Стены (коллизия) — через makeWall() → auto в walls[]
  makeWall(x, z, w, h, d, color);

  // 4. Пол-тайлы (поверхности для стояния) — через makePath() → auto в supportSurfaces[] + sceneDecor[]
  makePath(x, z, w, d, color);

  // 5. Ступени — через makeStep() → auto в steps[] + supportSurfaces[]
  makeStep(x, z, w, d, h, color);

  // 6. Декор (деревья, знаки, колонны) — через helper-функции → в sceneDecor[]
  makeTree(x, z);
  makeSign(x, y, z, rotY, text);
  makeColumn(x, z, specialDir); // колонна со знаками + и −

  // 7. Пасхалка — установить specialSignPos для detect в tick()
  specialSignPos = new THREE.Vector3(x, y, z);
}
```

## Массивы объектов (что куда добавлять)

| Массив | Удаляется из сцены | Очищается | Назначение |
|---|---|---|---|
| `walls[]` | ✅ rebuildWorld | ✅ | Коллизия (AABB) |
| `steps[]` | ✅ rebuildWorld | ✅ | Ступени (auto-climb) |
| `supportSurfaces[]` | ✅ через sceneDecor | ✅ | Поверхности для стояния |
| `sceneDecor[]` | ✅ rebuildWorld | ✅ | Всё визуальное |
| `floor` | ✅ вручную (по имени) | — | Одиночный пол |

## Критические правила

1. **Свет → всегда в sceneDecor[]** — иначе при каждом переходе между уровнями добавляется новый, яркость растёт
2. **makePath → уже добавляет в sceneDecor[]** (добавлено в исходнике)
3. **floor.position.y = -0.02** — чуть ниже y=0, чтобы не было z-fighting с объектами на полу
4. **specialSignPos = null** в начале buildLevelN — сбросить до установки
5. **Перекрывающиеся PlaneGeometry** на одном Y дают z-fighting — использовать неперекрывающиеся тайлы
6. **Свет и ambient в buildLevel1/2** не нужны отдельно — там работают глобальные (lines 159-172)

## Система переходов между уровнями

- Лава (level 2 → 3): `startLavaSequence()` — анимация падения + respawn
- Корабль (level 3 → 4): `triggerShipExplosion()` → confetti → `state.level = 4; rebuildWorld(); respawnAt(...)`
- Для нового перехода: добавить условие в `tick()` или новую `state.level = N; rebuildWorld(); respawnAt(...)`

## Interact-пасхалка

В tick():
```javascript
} else if (state.level === N) {
  if (specialSignPos && pos.distanceTo(specialSignPos) < 2.5 && !state.foundEggN) {
    state.foundEggN = true;
    showMessage('...', 5000);
  }
}
```

## Helper-функции (какие есть)

- `makeWall(x, z, w, h, d, color)` — стена-куб
- `makePath(x, z, w, d, color)` — пол-тайл, на нём можно стоять
- `makeStep(x, z, w, d, h, color)` — ступень (auto-climb до 1.0 unit)
- `makeSign(x, y, z, rotY, text)` — деревянная табличка с текстом
- `makeWallArrow(x, y, z, rotY, emoji, label)` — стрелка на стене
- `makeTree(x, z, crownColor)` — дерево
- `makePond(x, z, radius, color)` — лужа (вода или лава)
- `makeLunarRock(x, z, size, color)` — камень-сфера
- `makeColumn(cx, cz, specialDir)` — колонна со знаками +/−, specialDir = 'N'|'S'|'E'|'W'
- `makeTorch4(x, z)` — факел (sceneDecor + PointLight)
- `makeBookshelf(x, z, rotY)` — книжный стеллаж

**Why:** без этих правил уровни оставляют мусор в сцене (старые огни, пути, декор) и вызывают визуальные баги и тряску при переходах.
**How to apply:** при создании каждого нового уровня — сверяться с этим списком перед коммитом.
