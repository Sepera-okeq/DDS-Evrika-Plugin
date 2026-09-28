# DDS Evrika Plugin for Krita

[![Build](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/actions/workflows/release.yml/badge.svg)](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/actions/workflows/release.yml)
[![Release](https://img.shields.io/github/v/release/Sepera-okeq/DDS-Evrika-Plugin)](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/releases/latest)
![Krita](https://img.shields.io/badge/Krita-5.x%20%7C%206.x-3babff)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**English** | [Русский](README.ru.md)

Open and save DirectDraw Surface (`.dds`) textures directly from Krita: BC1–BC7 compression,
sRGB or linear color space, mipmaps for any texture size.

## Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Export options](#export-options)
- [Encoders](#encoders)
- [Troubleshooting](#troubleshooting)
- [Building from source](#building-from-source)
- [Adding a translation](#adding-a-translation)
- [License](#license)

## Features

- **Import** DDS (DXT1–5, BC4, BC5, BC7, uncompressed, including `*_SRGB` variants) as a new Krita document.
- **Export** to BC1/DXT1, BC2/DXT3, BC3/DXT5, BC4, BC5, BC7 or uncompressed RGBA8.
- **sRGB or linear** output: `BC7_UNORM_SRGB` for color maps, `BC7_UNORM` for normal maps, masks and other data.
- **Mipmaps for any size**, not only power-of-two: full chain, none, or a fixed number of levels.
  In sRGB mode they are averaged in linear light, so they do not get darker.
- **Compression quality**: fast, normal, best.
- **Krita 5 (Qt5) and Krita 6 (Qt6)**.
- **Windows, Linux, macOS** (Intel and Apple Silicon); release archives include the tools they need.
- **Localized UI**: English and Russian, follows Krita's language, easy to extend.

## Installation

1. Download the archive for your system from the [latest release](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/releases/latest):

   | System | Archive | Included tools |
   |---|---|---|
   | Windows 10/11 x64 | `win-x64-dds_evrika_plugin-<version>.zip` | Cuttlefish, ImageMagick |
   | Linux x64 | `linux-x64-dds_evrika_plugin-<version>.zip` | Cuttlefish |
   | macOS 11+ (Intel and Apple Silicon) | `macos-universal-dds_evrika_plugin-<version>.zip` | Cuttlefish |
   | Anything else | `any-noarch-dds_evrika_plugin-<version>.zip` | none |

2. In Krita open **Tools → Scripts → Import Python Plugin from File...** and pick the archive.
   Do not unpack it.
3. Restart Krita. Make sure the plugin is enabled in
   **Settings → Configure Krita → Python Plugin Manager → DDS Evrika Plugin**.

### ImageMagick on Linux and macOS

Opening DDS files needs ImageMagick (export works without it thanks to Cuttlefish):

```sh
# macOS (Homebrew, native on Apple Silicon)
brew install imagemagick

# Debian / Ubuntu
sudo apt install imagemagick

# Fedora
sudo dnf install ImageMagick

# Arch
sudo pacman -S imagemagick
```

The plugin finds Homebrew and MacPorts installations even though Krita on macOS does not see your shell `PATH`.
You can also set the path manually in **DDS Evrika Settings**.

### Manual installation

Copy the contents of the `DDS_EVRIKA_PLUGIN` folder from the archive into Krita's resource folder
(**Settings → Manage Resources → Open Resource Folder**), `pykrita` subfolder:

| System | Folder |
|---|---|
| Windows | `%APPDATA%\krita\pykrita\` |
| Linux | `~/.local/share/krita/pykrita/` |
| macOS | `~/Library/Application Support/krita/pykrita/` |

You should get `pykrita/dds_evrika_plugin.desktop` and `pykrita/dds_evrika_plugin/`.

## Usage

All commands are in **Tools → Scripts**:

| Command | What it does |
|---|---|
| **Import DDS** | Opens a DDS file as a new document using the saved intermediate format. |
| **Import DDS as...** | Same, but asks for the intermediate format (PNG, TIFF, BMP, JPEG, TGA). |
| **Export DDS** | Saves the current document with the saved export settings. |
| **Export DDS as...** | Asks for the export settings first; tick *Remember these settings* to make them default. |
| **DDS Evrika Settings** | Default export options, encoder, tool paths, language. |

Export never changes the document's file name: the image is flattened into a temporary PNG, converted and the PNG is deleted.

## Export options

| Option | Values | Notes |
|---|---|---|
| Compression format | BC1/DXT1, BC2/DXT3, BC3/DXT5, BC4, BC5, BC7, uncompressed | BC2–BC7 need Cuttlefish. |
| Color space | sRGB, Linear | See below. |
| Mipmaps | Full chain, none, 1–12 extra levels | Works for any size, e.g. 1000×600. |
| Mipmap filter | Lanczos, Box, Triangle, Catrom, Mitchell, ... | Cuttlefish maps it to the closest of box / linear / cubic / b-spline / catmull-rom. |
| Compression quality | Fast, Normal, Best | Best is noticeably slower for BC7. |

**sRGB vs linear.** Use *sRGB* for color textures (albedo, UI, sprites): the file gets an `*_SRGB` format
and mipmaps are computed in linear light. Use *Linear* for data textures (normal, roughness, metallic, masks):
the file gets a `*_UNORM` format and pixel values are written unchanged. In both modes the pixel values
of the main image are exactly the ones you see in Krita; the option only changes how the GPU interprets them
and how mipmaps are filtered.

Which formats to choose:

- color with smooth alpha → **BC7** (or BC3/DXT5 for old engines);
- color without alpha → **BC7** or BC1/DXT1;
- normal map → **BC5**, linear;
- single channel mask → **BC4**, linear.

## Encoders

| | Cuttlefish | ImageMagick |
|---|---|---|
| Formats | BC1–BC7, RGBA8 | DXT1, DXT5, RGBA8 |
| sRGB flag in the file | yes (DX10 header) | no (legacy header) |
| Quality levels | yes | best = cluster fit |
| Used for import | no | yes |

With **Automatic** (default) the plugin uses Cuttlefish when it is available and falls back to ImageMagick.
If ImageMagick is selected and the format is not supported, you get an error instead of a silently different file.

## Troubleshooting

**"ImageMagick was not found"** — install ImageMagick (see above) or set the path to `magick`
in **DDS Evrika Settings**. The dialog shows which tools were detected.

**macOS: "cuttlefish cannot be opened because the developer cannot be verified"** — remove the quarantine flag:

```sh
xattr -dr com.apple.quarantine ~/Library/Application\ Support/krita/pykrita/dds_evrika_plugin/resources
```

**The file has no mipmaps** — check that *Mipmaps* is not set to *No mipmaps*. Versions before 1.3 created mipmaps
only for power-of-two images; this is fixed.

**BC7 looked like DXT5 / colors looked washed out** — before 1.3 ImageMagick silently wrote DXT5 instead
of BC7/DXT3 and could not mark files as sRGB. Use Cuttlefish (included in the release archives).

**Grayscale documents** — Cuttlefish cannot read grayscale images, the plugin converts them to RGB through
ImageMagick. Without ImageMagick convert the document to RGB first (**Image → Convert Image Color Space**).

## Building from source

```sh
git clone https://github.com/Sepera-okeq/DDS-Evrika-Plugin
cd DDS-Evrika-Plugin
python3 tools/build_release.py                    # all archives into ./dist
python3 tools/build_release.py --platform macos   # only one
```

The script downloads Cuttlefish (and portable ImageMagick for Windows) from their GitHub releases.
The Windows archive needs the `7z` command. Pinned versions can be changed with the
`CUTTLEFISH_VERSION` and `IMAGEMAGICK_VERSION` environment variables.

**macOS on Apple Silicon.** The official Cuttlefish build is universal (x86_64 + arm64), so the
`macos-universal` archive runs natively; ImageMagick from Homebrew is native as well. Nothing has to be rebuilt.
To use your own Cuttlefish build, compile it following its [README](https://github.com/akb825/Cuttlefish#building)
and put `bin/cuttlefish` with the `lib` folder into `dds_evrika_plugin/resources/cuttlefish/`
or set the path in the settings.

**Releases** are built by [GitHub Actions](.github/workflows/release.yml) on every push; pushing a tag `vX.Y.Z`
that matches `VERSION` in `dds_evrika_plugin.py` publishes a GitHub release with all archives.

### Project layout

```
DDS_EVRIKA_PLUGIN/
├── dds_evrika_plugin.desktop   Krita plugin descriptor
└── dds_evrika_plugin/
    ├── __init__.py             registers the extension
    ├── dds_evrika_plugin.py    Krita UI: actions, dialogs, settings (PyQt5/PyQt6)
    ├── dds_tools.py            tool discovery, DDS import/export (no Krita dependency)
    ├── i18n.py                 localization loader
    ├── locales/*.json          translations
    ├── Manual.html             manual shown in Krita's Python Plugin Manager
    └── resources/              bundled tools (filled by the build script)
tools/build_release.py          builds the release archives
```

## Adding a translation

1. Copy `DDS_EVRIKA_PLUGIN/dds_evrika_plugin/locales/en.json` to `<code>.json`, e.g. `de.json` or `pt_BR.json`.
2. Translate the values, keep the keys and `{placeholders}` unchanged, set `_language_name`.
3. Open a pull request. Missing keys fall back to English, CI reports them.

The language follows Krita's *Settings → Switch Application Language* and can be overridden in **DDS Evrika Settings**.

## License

[MIT](LICENSE). Release archives also contain third-party tools under their own licenses, the license files are
included next to them: [Cuttlefish](https://github.com/akb825/Cuttlefish) (Apache 2.0) with PVRTexLib
(Imagination Technologies) and, on Windows, [ImageMagick](https://imagemagick.org) (ImageMagick License).
