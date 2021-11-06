# Debayer
Debayer is a commandline tool to convert camera raw images into scene-linear exr.

# Dependencies
- [OpenImageIO](https://github.com/OpenImageIO/oiio) - oiiotool is used for converting debayered tif images to exr.
- **Debayer Engines**
  - [RawTherapee](https://rawtherapee.com/downloads) - Powerful raw development software used to decode raw images. High quality, debayer algorithms, and more advanced raw processing like chromatic aberration removal.
  - [LibRaw](https://www.libraw.org/download) - dcraw_emu commandline utility included with LibRaw. Optional alternative for debayer. Simple, fast and effective.
  - [Darktable](https://www.darktable.org) - Uses darktable-cli plus an xmp config to process.
  - [vkdt](https://jo.dreggn.org/vkdt) - uses vkdt-cli to debayer.
## Commandline Options
    usage: debayer [-h] [-o OUTPUT] [-w] [-p PROFILE] [-ca] [-r RESIZE]
                [-e EXPOSURE] [-f FILTER]
                input_paths [input_paths ...]

    Debayer is a commandline tool to convert camera raw images into scene-linear
    exr.

    positional arguments:
    input_paths           Source(s) to process. Can be one or more images or
                            directories containing images.

    optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                            Output directory. If not specified, the current
                            directory will be used.
    -w, --overwrite       Overwrite existing output files.
    -p PROFILE, --profile PROFILE
                            Optional override to specify a custom rawtherapee pp3
                            profile to use. If none, the default config file will
                            be used.
    -ca, --aberration     Remove chromatic aberration (rawtherapee only)
    -r RESIZE, --resize RESIZE
                            Apply a resize to the output image. Aspect ratio is
                            not preserved if both width and height are specified.
                            <width>x<height>. (ML 1x3) 1920x2348 -> 5760x2348 ->
                            3840x1565 -> 2880x1174 (ML 1x3 2.35) - 1808x2300 ->
                            (unsqueeze) 5424x2300 -> (0.5) 2712x1150 Or 1280x2160
                            (1x3) -> 3840x2160 -> 2560x1440 -> 1920x1080 Or
                            preserve aspect ratio if w or h = 0: e.g. "1920x0" Can
                            also be a percentage like "50%"
    -e EXPOSURE, --exposure EXPOSURE
                            Raw to scene-linear exposure adjustment. Default is
                            4.0
    -f FILTER, --filter FILTER
                            Include only files that match regex. Can be comma
                            separated list.

## Configuration
First thing, you need to configure a few things in the debayer python file. At the top are a few variables you need to customize so debayer knows where to find the right executables.

Most importantly, you need to set the location of the rawtherapee-cli and oiiotool executable files (or dcraw_emu if using this instead of rawtherapee).
```
# Binary executable locations
OIIO_BIN    = '/usr/bin/oiiotool'
RT_BIN      = '/usr/bin/rawtherapee-cli'
DCRAW_BIN   = '/usr/bin/dcraw_emu'
DT_BIN      = '/usr/bin/darktable-cli'
VKDT_BIN    = '/opt/vkdt/vkdt/vkdt-cli'
```

You also need to specify a temp directory for debayer to use as a location for intermediate files (don't worry they are cleaned up automatically).
```
CACHE_DIR = '/var/tmp/debayer'
```

## Usage
Using debayer is very simple if you are familiar with commandline utilities. In the simplest possible form, you could write

```
debayer rawfile.cr2
```

This will process the raw file into the directory you are currently in.

If you want to specify a custom directory you could do
```
debayer rawfile.cr2 -o /path/to/output_dir
```

You can also process an entire source directory recursively. For example say you have this source directory structure:
```
/media/footage/20211012
└── dng
    ├── M22-1558
    │   ├── M22-1558.000000.dng
    │   ├── M22-1558.000001.dng
    │   ├── M22-1558.000002.dng
    │   ├── M22-1558.000003.dng
    │   ├── M22-1558.000004.dng
    └── M22-1600
        ├── M22-1600_000000.dng
        ├── M22-1600_000001.dng
        ├── M22-1600_000002.dng
        ├── M22-1600_000003.dng
        └── M22-1600_000004.dng
```

Say you want to recursively process all raw files inside /media/footage/20211012/dng, and output the results into /media/footage/20211012/exr. You could run
```
debayer /media/footage/20211012/dng -o /media/footage/20211012/exr

# or alternatively
cd /media/footage/20211012
debayer dng -o exr
```

## Exposure
One important parameter when debayering to scene-linear is how much to expose up with the `-e` parameter. Camera raw files are usually stored in an integer data format, which means the data is contained in a 0-1 container. How many bits of precision that data has within that container varies with the camera and sensor. 

To get this 0-1 data range into sensible scene-linear data, we need to expose up the raw data so that an 18% grey diffuse reflector will live at a scene-linear value of around 0.18. How much we need to expose up will of course depend on how the image was exposed in the camera. This also determines how much headroom you will have in highlights. A default value of 4.0 is provided as a starting point, but you will probably want to customize this depending on your source raw images.

## Custom Profile
You can specify a custom rawtherapee config pp3 file with `-p path/to/file.pp3`. This is useful if you need to customize whitebalance or sharpening settings for examples.

A default config is included in the repo and is used by default unless you change the `RT_DEFAULT_PROFILE` variable in the debayer code. This default profile outputs to linear ACEScg, and uses the RCD debayer algorithm, which is the best quality.

## Debayer Algorithms
If you are curious about the different available debayer algorithms in open software I have put together a big set of comparison images in jpg and exr available at this [mega.nz link](https://mega.nz/folder/ZEYg1bwL#jD1ED7P-D5srWdYR0PdP8A).

The images are processed with `dcraw_emu` for AHD, AAHD, DHT and VNG, and with `rawtherapee-cli` for RCD, DCB and AMaZE. The test images are a selection of 256x128 pixel crops of interesting image regions for judging debayer quality. My subjective ranking would be

```
RCD > DHT > DCB > AMaZE > AAHD > AHD > VNG
```

# Installation

## OpenImageIO
oiiotool can be installed with common pacakge managers on all platforms. [See this documentation](https://github.com/OpenImageIO/oiio/blob/master/INSTALL.md#installing-from-package-managers) for help.
## Rawtherapee
[Packages are provided](http://rawtherapee.com) for all platforms. However if you are on linux, the appimage won't give you access to the rawtherapee-cli commandline utility. You will need to install or compile it. There is a copr for many fedora and rhel distros [here](https://download.copr.fedorainfracloud.org/results/scx/rawtherapee/), which might help you.
## LibRaw
[LibRaw provides](https://www.libraw.org/download) packages for Windows and Mac, and for Linux it is easy to compile with minimal dependencies. I would recommend compiling from [master](https://github.com/LibRaw/LibRaw) to get the latest raw formats like Canon CR3.