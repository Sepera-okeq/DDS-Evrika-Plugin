# DDSEvrikaPlugin for Krita

## Overview

**DDSEvrikaPlugin** is a plugin for Krita that allows users to import and export DDS (DirectDraw Surface) files with advanced compression, mipmap, and filter options. The plugin relies on the power of ImageMagick to handle image format conversions and compressions, making it an ideal tool for texture creation and optimization in video games and 3D rendering environments.

With **DDSEvrikaPlugin**, you can:

- Import DDS files into Krita and convert them to editable formats.
- Export Krita documents using various DDS compression formats, including `dxt1`, `dxt3`, `dxt5`, `bc7`, and more.
- Customize export settings such as DDS compression type, mipmap levels, filter options, and file naming configuration.

## What's New in Version 1.2

- Added **filter support** during DDS export (available filters: Lanczos, Box, Triangle, Mitchell, and Catmull-Rom), enhancing the control over image resizing and quality.
- Improved **transparency handling**: Added guidelines for selecting an appropriate compression format (such as **DXT5**) to better handle textures with transparency or alpha channels.

## Features

1. **Import DDS**:
   - Directly import DDS textures into Krita.
   - Convert DDS files into formats such as PNG, TIFF, BMP, and others.

2. **Export DDS**:
   - Export images from Krita in DDS format using various compression options.
   - Choose advanced DDS compression formats: `dxt1`, `dxt3`, `dxt5`, `bc7`, or disable compression entirely with `none`.
   - Easily control mipmap levels for better texture resolution handling.
   - Apply filters like **Lanczos**, **Box**, **Mitchell**, among others, to control the image export quality.

3. **Settings Flexibility**:
   - Customize DDS file naming options (retain original names or create custom names).
   - Automatically save and reuse your preferred import/export settings for faster workflows.

4. **Improved Transparency Handling**:
   - When dealing with semi-transparent images, use **DXT5** compression to preserve smooth transitions in transparency.

5. **ImageMagick Integration**:
   - Leverage ImageMagick for robust image format conversions and compression processes.
  
6. **Localization Support**:
    - English
    - Russian

## Installation

### Step 1: Download the Plugin

- Download the latest plugin version from [the official release page](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/releases/latest).

### Step 2: Install Plugin

- Open [Krita](https://krita.org/) and go to Tools > Scripts > Import Python Plugins..., and select the zip archive. Confirm that you want to enable it.

### Step 3: Restart Krita

- Restart Krita to activate the plugin.

### Step 4: Enable the Plugin

- After restart, go to `Tools -> Scripts -> DDSEvrikaPlugin` to ensure that the plugin is available.

## Alternative Installation

### Step 1: Without ImageMagick included in the archive

- Download the latest plugin version from [the official release page](https://github.com/Sepera-okeq/DDS-Evrika-Plugin/releases/latest).

### Step 2: Locate Krita's Plugin Folder

- Extract the plugin into the appropriate folder depending on your operating system:
  - **Windows**: `C:\Users\<YourUser>\AppData\Roaming\krita\pykrita\`
  - **Linux**: `~/.local/share/krita/pykrita/`
  - **MacOS**: `~/Library/Application Support/krita/pykrita/`

### Step 3: Install ImageMagick

- Ensure ImageMagick is installed and the `magick` executable is accessible.
  - On **Windows**, place `magick.exe` in the `resources` folder inside the plugin.
  - On **Linux** and **MacOS**, ImageMagick should be globally installed via a package manager.

### Step 4: Restart Krita

- Restart Krita to activate the plugin.

### Step 5: Enable the Plugin

- After restart, go to `Tools -> Scripts -> DDSEvrikaPlugin` to verify that the plugin is available in the Krita interface.

## Usage Guide

### Import DDS Files

1. Navigate to `Tools -> Scripts -> Import DDS`.
2. Select the DDS file you want to convert.
3. Choose your preferred format (PNG, BMP, TIFF, etc.) for conversion.
4. The imported image will be editable in a new Krita document.

### Export DDS Files

1. Navigate to `Tools -> Scripts -> Export to DDS`.
2. Select the desired DDS compression format and mipmap level.
3. Choose a filter (such as **Lanczos**, **Box**, or **Mitchell**) for optimal quality.
4. The exported `.dds` file will be saved to your chosen directory.

### Import/Export with Advanced Settings

1. Use the `Import DDS as...` or `Export DDS as...` options to customize the format, compression, mipmap levels, and adjust file names.
2. Control export settings directly from the settings dialog via `Tools -> Scripts -> Evrika Settings`.

## Plugin Settings

- **Compression Formats**: Choose from `dxt1`, `dxt3`, `dxt5`, `bc7`, or none.
- **Mipmap Levels**: Choose automatic mipmap detection or select levels 1-5.
- **Image Filters**: Apply filters (Lanczos, Box, Mitchell, Catmull-Rom, Triangle) during the export process to manage image resizing quality.
- **File Naming**: Options to use original file names or generate custom names. Supports specifying custom export names.

## Requirements

- **Krita 4.2+**: Ensure you have Krita version 4.2 or higher.
- **ImageMagick**: Installed and configured in your system's PATH. Use the provided `magick.exe` for Windows systems, or install ImageMagick globally on Linux and macOS (`apt`/`brew`).

## Known Issues with Transparency

For images containing transparency or semi-transparent areas, it is recommended to use the **DXT5** compression format. **DXT1**, while efficient, supports only binary transparency, leading to the loss of partial transparency. If this compression format is selected in conjunction with filters like **Lanczos**, it may blend and remove transparency, so use **DXT5** to preserve a smooth transition.

## Support & Troubleshooting

### Common issues

1. **Issue: ImageMagick not found**
   - Ensure `magick` is installed and its location is in your **PATH**.
   - For Windows, verify `magick.exe` is in the `resources` folder of the plugin.

2. **Issue: DDS export fails**
   - Ensure the output file has the correct `.dds` extension.
   - Verify that the DDS compression format is supported by ImageMagick.
   - If you are working with transparency, make sure you're using **DXT5** to preserve the alpha channel.

3. **Krita crashes or the plugin doesn't appear**
   - Ensure the plugin is unzipped in the correct `pykrita` folder. Restart Krita after installation.

## Development

### Step 1: Clone the repository

- Clone the project: `git clone https://github.com/Sepera-okeq/DDS-Evrika-Plugin`

### Step 2: Install dependencies

- Install ImageMagick from the [official website](https://imagemagick.org/script/download.php) or via a package manager.
- Drop `magick.exe` in the `resources` folder (Windows).

### Step 3: Start developing

- Make your changes and test the plugin within Krita.

## Contributing

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-xyz`.
3. Commit your changes: `git commit -m "feat: Add new feature"`.
4. Push your branch: `git push origin feature-xyz`.
5. Open a pull request on GitHub.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Credits

- **PyQt5**: Python bindings for cross-platform GUIs.
- **ImageMagick**: Handling image conversions and compressions.
- **Krita**: An open-source painting software.
