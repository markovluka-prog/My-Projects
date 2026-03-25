# 3D Tool Instructions

## Инструмент
`/Users/lukamarkov/Library/Mobile Documents/com~apple~CloudDocs/My projects/Claude/tools/gltf_tool.py`

## Команды

```bash
# Создать GLB из сцены
python3 gltf_tool.py create scene.json output.glb

# Редактировать существующий GLB
python3 gltf_tool.py edit model.glb changes.json [output.glb]

# Информация о GLB
python3 gltf_tool.py info model.glb
```

Все команды запускаются из любой папки — указывать полные пути.

## scene.json — формат

```json
{
  "objects": [
    {
      "name": "unique_id",
      "type": "box",
      "position": [0, 0, 0],
      "rotation": [0, 0, 0],
      "scale": [1, 1, 1],
      "color": [0.5, 0.5, 0.5],
      "opacity": 1.0
    }
  ]
}
```

### Поля

| Поле | Обязательно | По умолчанию | Описание |
|------|-------------|--------------|----------|
| `name` | да | — | Уникальный ID объекта |
| `type` | да | — | Тип примитива |
| `position` | нет | [0,0,0] | Координаты центра [x,y,z] |
| `rotation` | нет | [0,0,0] | Углы Эйлера в градусах [rx,ry,rz] |
| `scale` | нет | [1,1,1] | Размеры [x,y,z] в единицах |
| `color` | нет | [0.5,0.5,0.5] | RGB цвет, значения 0.0–1.0 |
| `opacity` | нет | 1.0 | Прозрачность 0.0–1.0 |

### Типы примитивов

| Тип | Как используется scale |
|-----|----------------------|
| `box` | [ширина, глубина, высота] |
| `sphere` | [диаметр, _, _] (равномерный) |
| `cylinder` | [диаметр, _, высота] |
| `cone` | [диаметр основания, _, высота] |
| `plane` | [ширина, глубина, _] (очень тонкий) |

### Цвета (справочник)

```
Белый:      [1.0, 1.0, 1.0]
Чёрный:     [0.1, 0.1, 0.1]
Серый:      [0.5, 0.5, 0.5]
Бирюзовый:  [0.0, 0.5, 0.5]
Синий:      [0.1, 0.3, 0.8]
Красный:    [0.8, 0.1, 0.1]
Зелёный:    [0.1, 0.7, 0.2]
Жёлтый:     [1.0, 0.85, 0.0]
Оранжевый:  [1.0, 0.45, 0.0]
```

## changes.json — формат (для edit)

```json
{
  "add":    [ ...объекты в том же формате что scene.json... ],
  "remove": [ "name1", "name2" ],
  "modify": [ ...объекты с новыми значениями (по name)... ]
}
```

## Система координат

- Ось X: вправо
- Ось Y: вглубь
- Ось Z: вверх
- Единица = 1 см (рекомендуется)

## Просмотр

Установить расширение VS Code: `cesium.gltf-vscode`
Открыть .glb файл → автоматический 3D просмотр

## Зависимости

```bash
pip3 install trimesh numpy scipy
```

Уже установлены на этой машине.

## Пример: простая сцена

```json
{
  "objects": [
    {
      "name": "body",
      "type": "box",
      "position": [0, 0, 2],
      "scale": [2, 1, 3],
      "color": [0.1, 0.5, 0.5]
    },
    {
      "name": "head",
      "type": "sphere",
      "position": [0, 0, 4],
      "scale": [1.5, 1.5, 1.5],
      "color": [0.1, 0.1, 0.1]
    }
  ]
}
```

```bash
python3 "/Users/lukamarkov/Library/Mobile Documents/com~apple~CloudDocs/My projects/Claude/tools/gltf_tool.py" create scene.json model.glb
```
