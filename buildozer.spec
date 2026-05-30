[app]

# Название и пакет
title = NeuroPix
package.name = neuropix
package.domain = org.neuropix

# Исходники
source.dir = .
source.include_exts = py,ttf,db,png,jpg
source.include_patterns = assets/*

# Точка входа (Buildozer ищет main.py в корне)
# main.py

# Версия
version = 1.0

# Зависимости Python
requirements = python3==3.11.0,pygame==2.5.2

# Ориентация — портрет
orientation = portrait

# Иконка (нет — используется дефолтная)
# icon.filename = assets/icon.png

# Разрешения Android
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# API Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# ABI
android.archs = arm64-v8a, armeabi-v7a

# Убрать чёрные полосы при fullscreen на Android
android.allow_backup = True
android.wakelock = False

# Не показывать статус-бар
android.fullscreen = 1

# Gradle версия
android.gradle_dependencies =

# Buildozer log-level (0=quiet, 2=verbose)
log_level = 1

# Предупреждение: build в папку .buildozer/
# Для чистой сборки: buildozer android clean


[buildozer]

# Директория для временных файлов сборки
build_dir = ./.buildozer

# Директория для APK
bin_dir = ./bin
