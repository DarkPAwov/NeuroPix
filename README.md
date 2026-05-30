# NeuroPix Mobile 📱

Мобильная версия NeuroPix для Android. Портретная ориентация 480×854,
полностью сенсорное управление.

---

## Управление (сенсорное)

### МозгоБлок
- **← (левая половина экрана)** — двигать платформу влево
- **→ (правая половина экрана)** — двигать платформу вправо
- **◄ МЕНЮ** (верхний левый) — выход в меню

### ЭхоРяд
- **Касание плитки** — выбрать плитку
- **◄ МЕНЮ** (верхний левый) — выход

### ПространствоИкс
- **Кнопки A / B / C / D** — выбрать трансформацию
- **◄ МЕНЮ** (верхний левый) — выход

---

## Тестирование на ПК

```bash
pip install pygame>=2.5.0
python main.py
```

Игра откроется в окне 480×854. Мышь работает вместо касания.

---

## Сборка APK

> ⚠️ Buildozer требует **Linux**. На Windows используйте WSL 2 или GitHub Actions.

### Способ 1 — WSL 2 (Windows Subsystem for Linux)

**1. Установить WSL 2 (один раз):**
```powershell
# В PowerShell от администратора:
wsl --install
# Перезагрузить ПК, выбрать Ubuntu
```

**2. В терминале Ubuntu установить зависимости:**
```bash
sudo apt update && sudo apt install -y \
    python3-pip python3-venv git zip unzip \
    openjdk-17-jdk autoconf libtool \
    libffi-dev libssl-dev libbz2-dev \
    zlib1g-dev libncurses5-dev libsqlite3-dev \
    build-essential ccache

pip3 install --user buildozer cython==0.29.36
```

**3. Перейти в папку проекта и собрать:**
```bash
# Путь к папке в Windows доступен через /mnt/d/...
cd /mnt/d/New_Ind_Project/NeuroPix_Mobile

# Первая сборка (скачивает Android SDK/NDK — ~2-4 ГБ, занимает 10-30 мин):
~/.local/bin/buildozer android debug

# APK появится в папке:
# ./bin/neuropix-1.0-armeabi-v7a_arm64-v8a-debug.apk
```

**4. Установить APK на телефон:**
```bash
# Через ADB (телефон подключён USB, включена отладка):
adb install bin/*.apk

# Или скопировать APK на телефон и открыть файловым менеджером
```

---

### Способ 2 — GitHub Actions (облачная сборка, без WSL)

**1. Создать репозиторий на GitHub и загрузить папку NeuroPix_Mobile**

**2. Создать файл `.github/workflows/build.yml`:**
```yaml
name: Build APK

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            openjdk-17-jdk zip unzip \
            autoconf libtool libffi-dev libssl-dev \
            libbz2-dev zlib1g-dev libncurses5-dev \
            libsqlite3-dev build-essential ccache
          pip install buildozer cython==0.29.36

      - name: Build APK
        run: buildozer android debug

      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: neuropix-apk
          path: bin/*.apk
```

**3. Запустить Actions → скачать APK из артефактов**

---

### Способ 3 — Google Colab (быстро, бесплатно)

Открыть ноутбук: https://colab.research.google.com

```python
# Ячейка 1 — установка
!sudo apt-get install -y openjdk-17-jdk zip autoconf libtool \
    libffi-dev libssl-dev libbz2-dev zlib1g-dev build-essential
!pip install buildozer cython==0.29.36

# Ячейка 2 — загрузка проекта (zip файл загрузить через Files)
!unzip NeuroPix_Mobile.zip -d NeuroPix_Mobile
%cd NeuroPix_Mobile

# Ячейка 3 — сборка
!buildozer android debug

# Ячейка 4 — скачать APK
from google.colab import files
import glob
apk = glob.glob('bin/*.apk')[0]
files.download(apk)
```

---

## Структура проекта

```
NeuroPix_Mobile/
├── main.py                — точка входа (Android + desktop)
├── settings.py            — константы 480×854, большие шрифты
├── database.py            — SQLite рекорды
├── utils.py               — TouchState, Flash, HUD, ConfirmDialog
├── assets/
│   └── font_pixel.ttf     — скачивается автоматически
├── screens/
│   ├── menu.py            — вертикальное меню с карточками
│   ├── records.py         — таблица рекордов (вкладки)
│   └── name_input.py      — ввод имени (поддержка IME Android)
├── games/
│   ├── mozgoblok.py       — МозгоБлок (кнопки ←/→ внизу)
│   ├── echorad.py         — ЭхоРяд (большие плитки 116×116)
│   └── prostranstvo_x.py  — ПространствоИкс (кнопки A/B/C/D)
├── buildozer.spec         — конфигурация сборки Android
└── README.md
```

## Отличия от десктопной версии

| Параметр | Desktop | Mobile |
|----------|---------|--------|
| Разрешение | 800×600 горизонт. | 480×854 портрет |
| Управление | Клавиатура | Сенсор + FINGER-события |
| МозгоБлок | ← → клавиши | Зоны касания внизу |
| ЭхоРяд | 1-9 / мышь | Касание плитки (116px) |
| ПространствоИкс | A/B/C/D / мышь | Большие кнопки (68px) |
| Шрифты | xs=8, sm=12 | xs=10, sm=14 |
| Полный экран | F11 (опц.) | Всегда FULLSCREEN |
