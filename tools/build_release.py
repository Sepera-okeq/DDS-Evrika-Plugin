#!/usr/bin/env python3
"""Build release archives of DDSEvrikaPlugin for every OS.

Produces in ./dist:
  win-x64-dds_evrika_plugin-<version>.zip          plugin + Cuttlefish + portable ImageMagick
  linux-x64-dds_evrika_plugin-<version>.zip        plugin + Cuttlefish (ImageMagick from the system)
  macos-universal-dds_evrika_plugin-<version>.zip  plugin + Cuttlefish for Intel and Apple Silicon
  any-noarch-dds_evrika_plugin-<version>.zip       plugin only, tools are installed separately

Every archive can be installed with Krita's "Tools > Scripts > Import Python Plugin from File...".

Usage: python3 tools/build_release.py [--platform windows linux macos no-binaries]
Requires network access; the Windows build needs the `7z` command to unpack ImageMagick.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_SRC = os.path.join(ROOT, "DDS_EVRIKA_PLUGIN")
PLUGIN_NAME = "dds_evrika_plugin"
# Top-level folder inside the release archives.
ARCHIVE_ROOT = "DDS_EVRIKA_PLUGIN"
DIST = os.path.join(ROOT, "dist")

CUTTLEFISH_VERSION = os.environ.get("CUTTLEFISH_VERSION", "2.10.2")
IMAGEMAGICK_VERSION = os.environ.get("IMAGEMAGICK_VERSION", "7.1.2-32")

CUTTLEFISH_URL = "https://github.com/akb825/Cuttlefish/releases/download/v{v}/cuttlefish-{asset}"
CUTTLEFISH_LICENSE_URL = "https://raw.githubusercontent.com/akb825/Cuttlefish/v{v}/LICENSE.txt"
IMAGEMAGICK_URL = ("https://github.com/ImageMagick/ImageMagick/releases/download/"
                   "{v}/ImageMagick-{v}-portable-Q16-x64.7z")

PLATFORMS = ["windows", "linux", "macos", "no-binaries"]
# Archive names: <os>-<arch>-<plugin>-<version>.zip
ARCHIVE_PREFIX = {
    "windows": "win-x64",
    "linux": "linux-x64",
    "macos": "macos-universal",
    "no-binaries": "any-noarch",
}
# Files that must never end up in a release.
IGNORED = {"settings.json", "__pycache__", ".DS_Store"}


def plugin_version():
    with open(os.path.join(PLUGIN_SRC, PLUGIN_NAME, "dds_evrika_plugin.py"), encoding="utf-8") as f:
        return re.search(r'^VERSION = "([^"]+)"', f.read(), re.M).group(1)


def download(url, target):
    print("  downloading", url)
    with urllib.request.urlopen(url) as response, open(target, "wb") as f:
        shutil.copyfileobj(response, f)
    return target


def copy_plugin(stage):
    shutil.copy2(os.path.join(PLUGIN_SRC, PLUGIN_NAME + ".desktop"), stage)
    shutil.copytree(os.path.join(PLUGIN_SRC, PLUGIN_NAME), os.path.join(stage, PLUGIN_NAME),
                    ignore=lambda d, names: [n for n in names if n in IGNORED or
                                             (os.path.basename(d) == "resources" and n != "README.MD")])
    return os.path.join(stage, PLUGIN_NAME, "resources")


def unpack_cuttlefish(asset, work):
    archive = download(CUTTLEFISH_URL.format(v=CUTTLEFISH_VERSION, asset=asset),
                       os.path.join(work, asset))
    out = os.path.join(work, "cuttlefish-" + asset)
    if asset.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            z.extractall(out)
    else:
        with tarfile.open(archive) as t:
            t.extractall(out)
    return os.path.join(out, "cuttlefish")


def add_cuttlefish_unix(resources, work, asset, libraries):
    src = unpack_cuttlefish(asset, work)
    dst = os.path.join(resources, "cuttlefish")
    os.makedirs(os.path.join(dst, "bin"))
    os.makedirs(os.path.join(dst, "lib"))
    shutil.copy2(os.path.join(src, "bin", "cuttlefish"), os.path.join(dst, "bin"))
    # Symlinks do not survive Krita's zip import, so copy the real files under
    # the names the binaries were linked against.
    for name in libraries:
        shutil.copy2(os.path.realpath(os.path.join(src, "lib", name)), os.path.join(dst, "lib", name))


def add_windows_binaries(resources, work):
    src = unpack_cuttlefish("win64-tool.zip", work)
    shutil.copytree(src, os.path.join(resources, "cuttlefish"))

    archive = download(IMAGEMAGICK_URL.format(v=IMAGEMAGICK_VERSION), os.path.join(work, "im.7z"))
    im_dir = os.path.join(resources, "imagemagick")
    if not shutil.which("7z"):
        sys.exit("The `7z` command (7-Zip / p7zip) is required to unpack ImageMagick")
    subprocess.run(["7z", "x", "-y", "-o" + im_dir, archive], check=True, stdout=subprocess.DEVNULL)
    # Keep only the command line tool and its configuration files.
    for name in os.listdir(im_dir):
        path = os.path.join(im_dir, name)
        keep = name.lower() in ("magick.exe", "license.txt", "notice.txt") or name.lower().endswith(".xml")
        if not keep:
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    if not os.path.isfile(os.path.join(im_dir, "magick.exe")):
        sys.exit("magick.exe not found in the ImageMagick portable archive")


def write_zip(stage, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for directory, dirs, files in os.walk(stage):
            dirs.sort()
            # Krita's plugin importer finds the module by its directory entry
            # ("<name>/"), so directories must be stored explicitly.
            rel_dir = os.path.relpath(directory, stage).replace(os.sep, "/")
            z.write(directory, ARCHIVE_ROOT + "/" + ("" if rel_dir == "." else rel_dir + "/"))
            for name in sorted(files):
                path = os.path.join(directory, name)
                info = zipfile.ZipInfo.from_file(
                    path, ARCHIVE_ROOT + "/" + os.path.relpath(path, stage).replace(os.sep, "/"))
                info.compress_type = zipfile.ZIP_DEFLATED
                # Keep the executable bit for unzip tools that honor it.
                if os.access(path, os.X_OK) or "/bin/" in path.replace("\\", "/"):
                    info.external_attr = 0o100755 << 16
                with open(path, "rb") as f:
                    z.writestr(info, f.read())


def build(platform, version, work):
    print("Building", platform)
    stage = os.path.join(work, "stage-" + platform)
    os.makedirs(stage)
    resources = copy_plugin(stage)
    if platform == "windows":
        add_windows_binaries(resources, work)
    elif platform == "linux":
        add_cuttlefish_unix(resources, work, "linux.tar.gz", ["libcuttlefish.so.2.10", "libPVRTexLib.so"])
    elif platform == "macos":
        add_cuttlefish_unix(resources, work, "mac.tar.gz", ["libcuttlefish.2.10.dylib", "libPVRTexLib.dylib"])
    if platform != "no-binaries":
        download(CUTTLEFISH_LICENSE_URL.format(v=CUTTLEFISH_VERSION),
                 os.path.join(resources, "cuttlefish", "LICENSE.txt"))
    target = os.path.join(DIST, "{}-{}-{}.zip".format(ARCHIVE_PREFIX[platform], PLUGIN_NAME, version))
    write_zip(stage, target)
    print("  ->", os.path.relpath(target, ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", nargs="+", choices=PLATFORMS, default=PLATFORMS)
    args = parser.parse_args()
    version = plugin_version()
    os.makedirs(DIST, exist_ok=True)
    work = tempfile.mkdtemp(prefix="evrika_build_")
    try:
        for platform in args.platform:
            build(platform, version, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
