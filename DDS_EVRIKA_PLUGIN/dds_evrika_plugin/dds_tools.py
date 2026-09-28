"""Encoding/decoding helpers for DDSEvrikaPlugin.

This module does not depend on Krita or Qt, so it can be tested standalone.

Backends:
  * ImageMagick (``magick`` or IM6 ``convert``) - used for import (DDS -> image)
    and as a fallback encoder. It can only write DXT1, DXT5 and uncompressed DDS
    with a legacy header (no sRGB flag). Its own mipmap generator only works for
    power-of-two images, so the plugin always builds the mip chain itself and
    passes it with ``dds:mipmaps=fromlist``.
  * Cuttlefish (https://github.com/akb825/Cuttlefish) - preferred encoder. Writes
    DX10 DDS files with BC1-BC7, sRGB/linear formats, mipmaps for any size and
    compression quality levels.
"""

import os
import shutil
import stat
import struct
import subprocess
import sys

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(PLUGIN_DIR, "resources")

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

# GUI applications on macOS (and sometimes on Linux) do not inherit the shell
# PATH, so Homebrew/MacPorts binaries are not found by a bare "magick".
EXTRA_SEARCH_DIRS = [] if IS_WINDOWS else [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/opt/local/bin",
    "/usr/bin",
    "/snap/bin",
    os.path.expanduser("~/.local/bin"),
]

ENCODER_AUTO = "auto"
ENCODER_CUTTLEFISH = "cuttlefish"
ENCODER_IMAGEMAGICK = "imagemagick"
ENCODERS = [ENCODER_AUTO, ENCODER_CUTTLEFISH, ENCODER_IMAGEMAGICK]

# key -> (short name, cuttlefish format, supports sRGB, supported by ImageMagick)
# UI labels live in the locale files as "format_<key>".
COMPRESSION_FORMATS = {
    "dxt1": ("BC1/DXT1", "BC1_RGBA", True, True),
    "dxt3": ("BC2/DXT3", "BC2", True, False),
    "dxt5": ("BC3/DXT5", "BC3", True, True),
    "bc4": ("BC4", "BC4", False, False),
    "bc5": ("BC5", "BC5", False, False),
    "bc7": ("BC7", "BC7", True, False),
    "none": ("RGBA8", "R8G8B8A8", True, True),
}

COLORSPACE_SRGB = "srgb"
COLORSPACE_LINEAR = "linear"
COLORSPACES = [COLORSPACE_SRGB, COLORSPACE_LINEAR]

QUALITIES = ["fast", "normal", "best"]
CUTTLEFISH_QUALITY = {"fast": "low", "normal": "normal", "best": "highest"}

# "Auto" = full mip chain down to 1x1, "None" = only the main image,
# a number = amount of extra levels below the main image.
MIPMAP_CHOICES = ["Auto", "None"] + [str(i) for i in range(1, 13)]

FILTERS = ["Lanczos", "Undefined", "Point", "Box", "Triangle", "Hermite", "Hanning", "Hamming",
           "Blackman", "Gaussian", "Quadratic", "Cubic", "Catrom", "Mitchell", "Jinc", "Sinc",
           "SincFast", "Kaiser", "Welch", "Parzen", "Bohman", "Bartlett", "Lagrange",
           "LanczosSharp", "Lanczos2", "Lanczos2Sharp", "Robidoux", "RobidouxSharp", "Cosine",
           "Spline", "Sentinel"]

# Cuttlefish only has a handful of mip filters, map ImageMagick names to the closest one.
CUTTLEFISH_FILTER = {
    "point": "box",
    "box": "box",
    "triangle": "linear",
    "hermite": "linear",
    "bartlett": "linear",
    "cubic": "cubic",
    "mitchell": "cubic",
    "robidoux": "cubic",
    "spline": "b-spline",
    "gaussian": "b-spline",
    "quadratic": "b-spline",
}


class ToolError(Exception):
    """Raised when an external tool is missing or fails.

    ``code`` is a locale key (see locales/*.json), ``params`` are its format
    arguments and ``details`` is untranslated output such as the tool's stderr.
    """

    def __init__(self, code, details="", **params):
        super().__init__(code)
        self.code = code
        self.details = details
        self.params = params

    def __str__(self):
        text = "{} {}".format(self.code, self.params) if self.params else self.code
        return text + ("\n" + self.details if self.details else "")


def _ensure_executable(path):
    # Krita's "Import Python Plugin" extracts zip files without permission bits.
    if IS_WINDOWS or os.access(path, os.X_OK):
        return
    try:
        mode = os.stat(path).st_mode
        os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


def _is_file(path):
    return bool(path) and os.path.isfile(path)


def _which(name):
    found = shutil.which(name)
    if found:
        return found
    for directory in EXTRA_SEARCH_DIRS:
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def subprocess_env():
    """Environment for child processes.

    Krita's AppImage exports LD_LIBRARY_PATH/PYTHON* pointing to its bundled
    libraries, which can break system binaries such as ImageMagick.
    """
    env = dict(os.environ)
    if env.get("APPDIR") or env.get("APPIMAGE"):
        for key in ("LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH"):
            env.pop(key, None)
    extra = [d for d in EXTRA_SEARCH_DIRS if os.path.isdir(d)]
    if extra:
        env["PATH"] = os.pathsep.join([env.get("PATH", "")] + extra)
    return env


def run_tool(args):
    kwargs = {}
    if IS_WINDOWS:
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=subprocess_env(), **kwargs)
    except OSError as e:
        raise ToolError("err_tool_start", str(e), tool=args[0])
    if result.returncode != 0:
        output = (result.stderr or result.stdout or b"").decode("utf-8", "replace").strip()
        command = " ".join('"{}"'.format(a) if " " in a else a for a in args)
        raise ToolError("err_tool_failed", "{}\n\n$ {}".format(output, command),
                        tool=os.path.basename(args[0]), code=result.returncode)
    return result


def find_imagemagick(custom_path=""):
    """Return the path to ImageMagick (magick, or convert for IM6) or None."""
    if _is_file(custom_path):
        _ensure_executable(custom_path)
        return custom_path
    exe = "magick.exe" if IS_WINDOWS else "magick"
    for candidate in (os.path.join(RESOURCES_DIR, exe),
                      os.path.join(RESOURCES_DIR, "imagemagick", exe)):
        if _is_file(candidate):
            _ensure_executable(candidate)
            return candidate
    found = _which(exe)
    if found:
        return found
    if not IS_WINDOWS:
        # ImageMagick 6 (e.g. Debian/Ubuntu packages) has no "magick" binary.
        # On Windows "convert.exe" is a system tool, so never use it there.
        convert = _which("convert")
        if convert:
            try:
                if b"ImageMagick" in run_tool([convert, "-version"]).stdout:
                    return convert
            except ToolError:
                pass
    return None


def find_cuttlefish(custom_path=""):
    """Return the path to the Cuttlefish CLI or None."""
    if _is_file(custom_path):
        _ensure_executable(custom_path)
        return custom_path
    exe = "cuttlefish.exe" if IS_WINDOWS else "cuttlefish"
    base = os.path.join(RESOURCES_DIR, "cuttlefish")
    for candidate in (os.path.join(base, "bin", exe), os.path.join(base, exe)):
        if _is_file(candidate):
            _ensure_executable(candidate)
            return candidate
    return _which(exe)


def _png_header(path):
    with open(path, "rb") as f:
        header = f.read(26)
    if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ToolError("err_not_png", path=path)
    return header


def png_size(path):
    """Read width/height from a PNG header."""
    return struct.unpack(">II", _png_header(path)[16:24])


def png_is_grayscale(path):
    # IHDR color type: 0 - gray, 4 - gray + alpha.
    return _png_header(path)[25] in (0, 4)


def mip_sizes(width, height, mipmaps):
    """Sizes of the extra mip levels below the main image.

    mipmaps: "Auto" (full chain), "None" or a number of extra levels.
    """
    if mipmaps == "None":
        limit = 0
    elif mipmaps == "Auto":
        limit = None
    else:
        limit = int(mipmaps)
    sizes = []
    while (width > 1 or height > 1) and (limit is None or len(sizes) < limit):
        width = max(1, width // 2)
        height = max(1, height // 2)
        sizes.append((width, height))
    return sizes


def resolve_encoder(encoder, compression, magick_path, cuttlefish_path):
    """Pick the encoder, raising ToolError with a helpful message if impossible."""
    im_supported = COMPRESSION_FORMATS[compression][3]
    if encoder == ENCODER_CUTTLEFISH:
        if not cuttlefish_path:
            raise ToolError("err_cuttlefish_missing")
        return ENCODER_CUTTLEFISH
    if encoder == ENCODER_IMAGEMAGICK or not cuttlefish_path:
        if not magick_path:
            raise ToolError("err_no_encoder")
        if not im_supported:
            raise ToolError("err_im_format_unsupported", format=COMPRESSION_FORMATS[compression][0])
        return ENCODER_IMAGEMAGICK
    return ENCODER_CUTTLEFISH


def imagemagick_export_args(magick, src_png, dst_dds, compression, mipmaps, colorspace,
                            filter_name, quality):
    width, height = png_size(src_png)
    # Tag as sRGB without converting so ImageMagick never alters the pixel values.
    args = [magick, src_png, "-set", "colorspace", "sRGB"]
    if filter_name and filter_name != "Undefined":
        args += ["-filter", filter_name]
    for w, h in mip_sizes(width, height, mipmaps):
        args.append("(")
        args += ["-clone", "0"]
        if colorspace == COLORSPACE_SRGB:
            # Gamma-correct downscaling: average in linear light.
            args += ["-colorspace", "RGB", "-resize", "{}x{}!".format(w, h), "-colorspace", "sRGB"]
        else:
            args += ["-resize", "{}x{}!".format(w, h)]
        args.append(")")
    args += ["-define", "dds:mipmaps=fromlist", "-define", "dds:compression={}".format(compression)]
    if quality == "best" and compression != "none":
        args += ["-define", "dds:cluster-fit=true"]
        if compression == "dxt5":
            args += ["-define", "dds:weight-by-alpha=true"]
    args.append("DDS:" + dst_dds)
    return args


def cuttlefish_export_args(cuttlefish, src_png, dst_dds, compression, mipmaps, colorspace,
                           filter_name, quality):
    _, cf_format, srgb_capable, _ = COMPRESSION_FORMATS[compression]
    args = [cuttlefish, "-q", "-i", src_png, "-f", cf_format, "-t", "unorm"]
    if colorspace == COLORSPACE_SRGB and srgb_capable:
        # Stores a *_SRGB format and generates mipmaps in linear light.
        args.append("--srgb")
    if mipmaps != "None":
        args.append("-m")
        if mipmaps != "Auto":
            args.append(str(int(mipmaps) + 1))  # Cuttlefish counts the main image too.
        args.append(CUTTLEFISH_FILTER.get((filter_name or "").lower(), "catmull-rom"))
    args += ["-Q", CUTTLEFISH_QUALITY.get(quality, "normal")]
    args += ["--file-format", "dds", "-o", dst_dds]
    return args


def export_dds(src_png, dst_dds, compression="dxt5", mipmaps="Auto", colorspace=COLORSPACE_SRGB,
               filter_name="Lanczos", quality="normal", encoder=ENCODER_AUTO,
               magick_path="", cuttlefish_path=""):
    """Convert a PNG to DDS. Returns the name of the encoder that was used."""
    if compression not in COMPRESSION_FORMATS:
        raise ToolError("err_unknown_compression", format=compression)
    if mipmaps not in MIPMAP_CHOICES:
        mipmaps = "Auto"
    magick = find_imagemagick(magick_path)
    cuttlefish = find_cuttlefish(cuttlefish_path)
    used = resolve_encoder(encoder, compression, magick, cuttlefish)
    if used == ENCODER_CUTTLEFISH:
        if png_is_grayscale(src_png):
            # Cuttlefish cannot load grayscale PNG files.
            if not magick:
                raise ToolError("err_cuttlefish_gray")
            rgba_png = os.path.splitext(src_png)[0] + "_rgba.png"
            run_tool([magick, src_png, "-set", "colorspace", "sRGB", "-type", "TrueColorAlpha",
                      "PNG32:" + rgba_png])
            src_png = rgba_png
        args = cuttlefish_export_args(cuttlefish, src_png, dst_dds, compression, mipmaps,
                                      colorspace, filter_name, quality)
    else:
        args = imagemagick_export_args(magick, src_png, dst_dds, compression, mipmaps,
                                       colorspace, filter_name, quality)
    run_tool(args)
    return used


# ImageMagick's reader does not know most *_SRGB DXGI formats. The pixel data
# is identical to the UNORM variant, only the interpretation differs.
DXGI_SRGB_TO_UNORM = {
    29: 28,  # R8G8B8A8
    72: 71,  # BC1
    75: 74,  # BC2
    78: 77,  # BC3
    91: 87,  # B8G8R8A8
    93: 88,  # B8G8R8X8
}
DXGI_BC4_UNORM = 80
DDS_HEADER_SIZE = 128
DX10_HEADER_SIZE = 20


def _readable_dds_copy(src_dds, work_dir):
    """Rewrite a DX10 DDS that ImageMagick cannot read into one it can.

    Returns (path, extra ImageMagick args) or None if the file cannot be helped.
    Only the main image is kept.
    """
    with open(src_dds, "rb") as f:
        data = f.read()
    if len(data) < DDS_HEADER_SIZE + DX10_HEADER_SIZE or data[:4] != b"DDS " or data[84:88] != b"DX10":
        return None
    dxgi = struct.unpack_from("<I", data, DDS_HEADER_SIZE)[0]
    out_path = os.path.join(work_dir, "readable.dds")
    if dxgi in DXGI_SRGB_TO_UNORM:
        patched = bytearray(data)
        struct.pack_into("<I", patched, DDS_HEADER_SIZE, DXGI_SRGB_TO_UNORM[dxgi])
        with open(out_path, "wb") as f:
            f.write(patched)
        return out_path, []
    if dxgi == DXGI_BC4_UNORM:
        # A BC4 block is exactly a DXT5 alpha block: store it as DXT5 alpha with
        # black color blocks and extract the alpha channel afterwards.
        height, width = struct.unpack_from("<II", data, 12)
        blocks = ((width + 3) // 4) * ((height + 3) // 4)
        payload = data[DDS_HEADER_SIZE + DX10_HEADER_SIZE:]
        if len(payload) < blocks * 8:
            return None
        header = bytearray(data[:DDS_HEADER_SIZE])
        struct.pack_into("<I", header, 28, 1)  # mipmap count
        header[84:88] = b"DXT5"
        body = bytearray()
        empty_color = b"\x00" * 8
        for i in range(blocks):
            body += payload[i * 8:i * 8 + 8]
            body += empty_color
        with open(out_path, "wb") as f:
            f.write(header)
            f.write(body)
        return out_path, ["-alpha", "extract"]
    return None


def import_dds(src_dds, dst_image, magick_path="", work_dir=None):
    """Convert the main image of a DDS file to a regular image format."""
    magick = find_imagemagick(magick_path)
    if not magick:
        raise ToolError("err_magick_missing")
    # [0] - only the main image, without mipmaps / array slices.
    try:
        run_tool([magick, src_dds + "[0]", dst_image])
    except ToolError:
        readable = _readable_dds_copy(src_dds, work_dir or os.path.dirname(dst_image))
        if readable is None:
            raise
        path, extra = readable
        try:
            run_tool([magick, path + "[0]"] + extra + [dst_image])
        finally:
            os.remove(path)
