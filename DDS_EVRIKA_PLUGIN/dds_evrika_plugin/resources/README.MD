# resources

External command line tools used by the plugin. Release archives already contain
everything for their OS; this folder is only relevant when you install from source.

The plugin looks for the tools in this order:

1. The path set in **Tools > Scripts > DDS Evrika Settings**.
2. This folder:
   - `cuttlefish/bin/cuttlefish` (Linux, macOS) or `cuttlefish/cuttlefish.exe` (Windows)
     from <https://github.com/akb825/Cuttlefish/releases>, keep the `lib` folder next to `bin`;
   - `magick.exe` or `imagemagick/magick.exe` (Windows) from the ImageMagick
     *portable* build, `magick` (Linux, macOS).
3. `PATH` and the usual install folders (`/opt/homebrew/bin`, `/usr/local/bin`,
   `/opt/local/bin`, `/usr/bin`). ImageMagick 6 `convert` is also accepted on Linux/macOS.

`python3 tools/build_release.py` downloads and places these files automatically.
