# DDSEvrikaPlugin for Krita

## Overview

**DDSEvrikaPlugin** is a plugin for Krita that allows you to import and export DDS (DirectDraw Surface) files with advanced compression options, leveraging the power of ImageMagick. The plugin enables artists and users to easily handle DDS formats, which are commonly used in game development and texture management.

With **DDSEvrikaPlugin**, you can:
- Import DDS files into Krita.
- Export DDS files with various compression formats, including `dxt1`, `dxt3`, `dxt5`, `bc7`, and more.
- Customizable export settings, such as compression type and mipmap levels.

---

## Features

1. **Import DDS:**
   - Import DDS textures directly into Krita.
   - Convert DDS into editable image formats like PNG, BMP, TIFF, etc.
   
2. **Export DDS:**
   - Export Krita documents to DDS formats.
   - Advanced DDS compression settings: `dxt1`, `dxt3`, `dxt5`, `bc7`, `none`.
   - Specify the levels of mipmaps for detailed texture control.
   
3. **Powered by ImageMagick:**
   - Uses ImageMagick for robust image and compression handling.
   - Seamless conversion between formats.
  
4. **Localization**
    - English
    - Russian

---

## Install

You can download the current version of the plugin [here](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/releases/latest).

---

## Requirements

- **Krita** version 4.2 or higher.
- **ImageMagick** installed and accessible via the command line.
  - On **Windows**, ensure that `magick.exe` is placed in the `resources` folder (you can configure its path manually).
  - On **Linux** and **MacOS**, ensure that `magick` is installed globally via your package manager (`apt`, `brew`, etc.).

---

## Develop

1. **Download the plugin**:
   - Clone this repository or download it as a ZIP.

2. **Install ImageMagick**:
   - Windows/Linux/MacOS: Download and install ImageMagick from the [official website](https://imagemagick.org/script/download.php).
   - Drop in path installing plugin, t.e `installing_plugin\dds_evrika_plugin\resources`

3. **Installing the plugin**:
   - Extract or clone the plugin into Krita’s `pykrita` folder. You can find this folder in different locations depending on your OS:
     - **Windows**: `C:\Users\<YourUserName>\AppData\Roaming\krita\pykrita\`
     - **Linux**: `~/.local/share/krita/pykrita/`
     - **MacOS**: `~/Library/Application Support/krita/pykrita/`
  
4. **Restart Krita**:
   - After installing the plugin, restart Krita to activate the plugin.

5. **Verify the Installation**:
   - Go to `Tools -> Scripts -> DDSEvrikaPlugin` to see the new options under the tools menu.

---

## Usage

Once **DDSEvrikaPlugin** is installed and activated, you can start importing and exporting DDS files directly within Krita.

- **Importing a DDS File**:
  1. Select `Tools -> Scripts -> Import DDS`.
  2. Choose the DDS file you wish to import.
  3. Optionally choose the image format for conversion (e.g. PNG, BMP, TIFF).
  4. The file will be imported into a new Krita document.

- **Exporting to DDS**:
  1. Select `Tools -> Scripts -> Export to DDS`.
  2. Choose the options for compression and other settings via the dialog box:
     - **Format Selection**: `png`, `tiff`, `bmp`, etc.
     - **DDS Compression**: `dxt1`, `dxt3`, `dxt5`, `bc7`, or no compression.
     - **Mipmap Levels**: Choose the number of mipmaps, or let it be auto-detected.
  3. The file will be saved as a `.dds` file in the chosen directory.

---

## Plugin Options

### Compression Formats

You can export DDS files using various compression methods supported by ImageMagick:

- `dxt1`: Provides compression with 1-bit alpha (transparency) or none.
- `dxt3`: For textures with 4-bit explicit alpha channels (better transparency).
- `dxt5`: Uses interpolated alpha values for better gradient textures.
- `bc7`: High-performance compression, common in modern engines.
- `none`: No compression (raw format).

### Mipmap Levels

Mipmaps are used in textures to improve rendering performance. The plugin supports multiple levels of mipmaps for better control of texture quality:

- `Auto`: Automatically detects mipmap levels.
- Custom levels: Choose from `1`, `2`, `3`, `4`, `5`, etc.

---

## Troubleshooting

1. **ImageMagick not found**:
   - Ensure that ImageMagick is properly installed on your system and available in your system's PATH.
   - On Windows, confirm that the `magick.exe` file is located in the `resources` folder inside the plugin directory.

2. **DDS Export fails**:
   - Make sure that the output file path has the correct `.dds` extension.
   - Check that the selected DDS compression format is supported.

4. **Other issues**:
   - If Krita crashes or the plugin doesn't appear after installation, check if you have installed the plugin in the correct `pykrita` directory. Ensure you restart Krita after installation.

---

## Contributing

If you wish to contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-xyz`
3. Commit your changes: `git commit -m "Add some feature"`
4. Push to the branch: `git push origin feature-xyz`
5. Submit a pull request.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Credits

- **PyQt5**: The Python bindings for the Qt framework.
- **ImageMagick**: Used to handle image conversion and compression.
- **Krita**: An amazing open-source painting software.
