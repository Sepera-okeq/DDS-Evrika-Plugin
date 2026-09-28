# DDS Evrika Plugin для Krita

[![Build](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/actions/workflows/release.yml/badge.svg)](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/actions/workflows/release.yml)
[![Release](https://img.shields.io/github/v/release/Sepera-okeq/DDS-Evrika-Plugin)](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/releases/latest)
![Krita](https://img.shields.io/badge/Krita-5.x%20%7C%206.x-3babff)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English](README.md) | **Русский**

Открывайте и сохраняйте текстуры DirectDraw Surface (`.dds`) прямо из Krita: сжатие BC1–BC7,
цветовое пространство sRGB или linear, mipmap для текстур любого размера.

## Содержание

- [Возможности](#возможности)
- [Установка](#установка)
- [Использование](#использование)
- [Параметры экспорта](#параметры-экспорта)
- [Кодировщики](#кодировщики)
- [Решение проблем](#решение-проблем)
- [Сборка из исходников](#сборка-из-исходников)
- [Добавление перевода](#добавление-перевода)
- [Лицензия](#лицензия)

## Возможности

- **Импорт** DDS (DXT1–5, BC4, BC5, BC7, без сжатия, включая варианты `*_SRGB`) в новый документ Krita.
- **Экспорт** в BC1/DXT1, BC2/DXT3, BC3/DXT5, BC4, BC5, BC7 или несжатый RGBA8.
- **sRGB или linear**: `BC7_UNORM_SRGB` для цветных карт, `BC7_UNORM` для нормалей, масок и прочих данных.
- **Mipmap для любого размера**, не только для степеней двойки: полная цепочка, без mipmap или заданное число уровней.
  В режиме sRGB они усредняются в линейном свете и не темнеют.
- **Качество сжатия**: быстро, нормально, максимум.
- **Krita 5 (Qt5) и Krita 6 (Qt6)**.
- **Windows, Linux, macOS** (Intel и Apple Silicon); в архивах релиза уже есть нужные программы.
- **Локализация**: английский и русский, язык берётся из Krita, легко добавить новый.

## Установка

1. Скачайте архив для своей системы из [последнего релиза](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/releases/latest):

   | Система | Архив | Что внутри |
   |---|---|---|
   | Windows 10/11 x64 | `win-x64-dds_evrika_plugin-<версия>.zip` | Cuttlefish, ImageMagick |
   | Linux x64 | `linux-x64-dds_evrika_plugin-<версия>.zip` | Cuttlefish |
   | macOS 11+ (Intel и Apple Silicon) | `macos-universal-dds_evrika_plugin-<версия>.zip` | Cuttlefish |
   | Другое | `any-noarch-dds_evrika_plugin-<версия>.zip` | только плагин |

2. В Krita откройте **Инструменты → Сценарии → Импортировать модуль Python из файла...** и выберите архив.
   Распаковывать его не нужно.
3. Перезапустите Krita. Проверьте, что плагин включён в
   **Настройка → Настроить Krita → Менеджер модулей Python → DDS Evrika Plugin**.

### ImageMagick на Linux и macOS

Для открытия DDS нужен ImageMagick (экспорт работает и без него, через Cuttlefish):

```sh
# macOS (Homebrew, нативно на Apple Silicon)
brew install imagemagick

# Debian / Ubuntu
sudo apt install imagemagick

# Fedora
sudo dnf install ImageMagick

# Arch
sudo pacman -S imagemagick
```

Плагин сам находит установки Homebrew и MacPorts, хотя Krita на macOS не видит `PATH` из терминала.
Путь можно указать вручную в **Настройках DDS Evrika**.

### Ручная установка

Скопируйте содержимое папки `DDS_EVRIKA_PLUGIN` из архива в папку ресурсов Krita
(**Настройка → Управление ресурсами → Открыть папку ресурсов**), подпапку `pykrita`:

| Система | Папка |
|---|---|
| Windows | `%APPDATA%\krita\pykrita\` |
| Linux | `~/.local/share/krita/pykrita/` |
| macOS | `~/Library/Application Support/krita/pykrita/` |

Должны получиться `pykrita/dds_evrika_plugin.desktop` и `pykrita/dds_evrika_plugin/`.

## Использование

Все команды находятся в **Инструменты → Сценарии**:

| Команда | Что делает |
|---|---|
| **Импортировать DDS** | Открывает DDS как новый документ через сохранённый промежуточный формат. |
| **Импортировать DDS как...** | То же, но спрашивает промежуточный формат (PNG, TIFF, BMP, JPEG, TGA). |
| **Экспортировать DDS** | Сохраняет текущий документ с сохранёнными настройками экспорта. |
| **Экспортировать DDS как...** | Сначала спрашивает настройки; галочка *Запомнить эти настройки* делает их настройками по умолчанию. |
| **Настройки DDS Evrika** | Параметры экспорта по умолчанию, кодировщик, пути к программам, язык. |

Экспорт не меняет имя файла документа: изображение сводится во временный PNG, конвертируется, и PNG удаляется.

## Параметры экспорта

| Параметр | Значения | Примечание |
|---|---|---|
| Формат сжатия | BC1/DXT1, BC2/DXT3, BC3/DXT5, BC4, BC5, BC7, без сжатия | BC2–BC7 требуют Cuttlefish. |
| Цветовое пространство | sRGB, Linear | См. ниже. |
| Mipmap-уровни | Полная цепочка, без mipmap, 1–12 дополнительных | Работает для любого размера, например 1000×600. |
| Фильтр mipmap | Lanczos, Box, Triangle, Catrom, Mitchell, ... | Cuttlefish берёт ближайший из box / linear / cubic / b-spline / catmull-rom. |
| Качество сжатия | Быстро, Нормально, Максимум | Максимум для BC7 заметно медленнее. |

**sRGB или linear.** *sRGB* — для цветных текстур (albedo, интерфейс, спрайты): файл получает формат `*_SRGB`,
mipmap считаются в линейном свете. *Linear* — для текстур-данных (нормали, roughness, metallic, маски):
формат `*_UNORM`, значения пикселей записываются как есть. В обоих режимах значения основного изображения
совпадают с тем, что вы видите в Krita; параметр меняет только то, как их читает видеокарта и как фильтруются mipmap.

Что выбирать:

- цвет с плавной альфой → **BC7** (или BC3/DXT5 для старых движков);
- цвет без альфы → **BC7** или BC1/DXT1;
- карта нормалей → **BC5**, linear;
- одноканальная маска → **BC4**, linear.

## Кодировщики

| | Cuttlefish | ImageMagick |
|---|---|---|
| Форматы | BC1–BC7, RGBA8 | DXT1, DXT5, RGBA8 |
| Флаг sRGB в файле | да (заголовок DX10) | нет (старый заголовок) |
| Уровни качества | да | максимум = cluster fit |
| Используется для импорта | нет | да |

В режиме **Автоматически** (по умолчанию) используется Cuttlefish, а если его нет — ImageMagick.
Если выбран ImageMagick, а формат он не поддерживает, будет понятная ошибка, а не молча другой файл.

## Решение проблем

**«ImageMagick не найден»** — установите ImageMagick (см. выше) или укажите путь к `magick`
в **Настройках DDS Evrika**. В окне настроек видно, какие программы найдены.

**macOS: «cuttlefish не может быть открыт, так как разработчик не проверен»** — снимите карантин:

```sh
xattr -dr com.apple.quarantine ~/Library/Application\ Support/krita/pykrita/dds_evrika_plugin/resources
```

**В файле нет mipmap** — проверьте, что в *Mipmap-уровни* не выбрано *Без mipmap*. До версии 1.3 mipmap создавались
только для изображений со сторонами-степенями двойки; это исправлено.

**BC7 выглядел как DXT5 / цвета были блёклыми** — до 1.3 ImageMagick молча записывал DXT5 вместо BC7/DXT3 и не умел
помечать файл как sRGB. Используйте Cuttlefish (он есть в архивах релиза).

**Документы в оттенках серого** — Cuttlefish их не читает, плагин конвертирует их в RGB через ImageMagick.
Без ImageMagick сначала переведите документ в RGB (**Изображение → Преобразовать цветовое пространство**).

## Сборка из исходников

```sh
git clone https://github.com/Sepera-okeq/DDS-Evrika-Plugin
cd DDS-Evrika-Plugin
python3 tools/build_release.py                    # все архивы в ./dist
python3 tools/build_release.py --platform macos   # только один
```

Скрипт скачивает Cuttlefish (и портативный ImageMagick для Windows) из их релизов на GitHub.
Для Windows-архива нужна команда `7z`. Версии можно поменять переменными окружения
`CUTTLEFISH_VERSION` и `IMAGEMAGICK_VERSION`.

**macOS на Apple Silicon.** Официальная сборка Cuttlefish универсальная (x86_64 + arm64), поэтому архив
`macos-universal` работает нативно; ImageMagick из Homebrew тоже нативный. Пересобирать ничего не нужно.
Чтобы использовать свою сборку Cuttlefish, соберите его по [README](https://github.com/akb825/Cuttlefish#building)
и положите `bin/cuttlefish` вместе с папкой `lib` в `dds_evrika_plugin/resources/cuttlefish/`
или укажите путь в настройках.

**Релизы** собирает [GitHub Actions](.github/workflows/release.yml) при каждом push; push тега `vX.Y.Z`,
совпадающего с `VERSION` в `dds_evrika_plugin.py`, публикует релиз со всеми архивами.

## Добавление перевода

1. Скопируйте `DDS_EVRIKA_PLUGIN/dds_evrika_plugin/locales/en.json` в `<код>.json`, например `de.json` или `pt_BR.json`.
2. Переведите значения, не меняя ключи и `{подстановки}`, заполните `_language_name`.
3. Откройте pull request. Отсутствующие ключи берутся из английского, CI их покажет.

Язык следует за *Настройка → Сменить язык приложения* в Krita и может быть переопределён в **Настройках DDS Evrika**.

## Лицензия

[MIT](LICENSE). Архивы релиза также содержат сторонние программы под их собственными лицензиями, файлы лицензий
лежат рядом с ними: [Cuttlefish](https://github.com/akb825/Cuttlefish) (Apache 2.0) с PVRTexLib
(Imagination Technologies) и, для Windows, [ImageMagick](https://imagemagick.org) (ImageMagick License).
