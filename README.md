# Debayer
Debayer is a commandline tool to convert camera raw images into scene-linear exr.

# Dependencies
The only required dependency is oiiotool. However other "debayer engines" are also supported.

- [OpenImageIO](https://github.com/OpenImageIO/oiio) - oiiotool is used for converting debayered tif images to exr.
- **Debayer Engines**
  - [RawTherapee](https://rawtherapee.com/downloads) - Powerful raw development software used to decode raw images. High quality, good selection of debayer algorithms, and more advanced raw processing like chromatic aberration removal.
  - [LibRaw](https://www.libraw.org/download) - dcraw_emu commandline utility included with LibRaw. Optional alternative for debayer. Simple, fast and effective.
  - [Darktable](https://www.darktable.org) - Uses darktable-cli plus an xmp config to process.
  - [vkdt](https://jo.dreggn.org/vkdt) - uses vkdt-cli to debayer. Pretty experimental still. Uses Vulkan for image processing. Stupidly fast. Pretty limited.



## Configuration
You need to configure a few things in the debayer python file. At the top are some variables you need to customize. Described below are the important ones and what they do.

First you need to choose which debayer engine you will use. `DEBAYER_ENGINES` lists all possibilities. `DEBAYER_ENGINE` is where you set which debayer software will be used.
```
# Debayer engine options
DEBAYER_ENGINES = ['rt', 'art', 'dc', 'dcrcd', 'dt', 'vkdt', 'oiio'] 
# Debayer engine to use
DEBAYER_ENGINE = 'rt'
```
This configuration will use RawTherapee as the debayer engine.

IMPORTANT: If you are using RawTherapee 5.8 or lower, you need to [install an output icc profile](docs/RawTherapee.md).

Next you need to set the paths to the binary executable files. oiiotool is required. You only need to specify paths for the debayer engine you will use.

```
# Binary executable locations
OIIO_BIN    = '/usr/bin/oiiotool'
RT_BIN      = '/usr/bin/rawtherapee-cli'
ART_BIN     = '/usr/bin/ART-cli'
DCRAW_BIN   = '/usr/bin/dcraw_emu'
DT_BIN      = '/usr/bin/darktable-cli'
VKDT_BIN    = '/opt/vkdt/vkdt/vkdt-cli'
```

You also need to specify a temp directory for debayer to use as a location for intermediate files (don't worry they are cleaned up automatically). It speeds things up if this is on a fast local drive.

```
CACHE_DIR = '/var/tmp/debayer'
```

You can set other options as well:
`THREADS = 2` - Number of simultaneous jobs (Useful if using a single-threaded debayer engine like dcraw).

`EXR_COMPRESSION = 'dwaa:15'` - Type of compression to use for output exr files.

`DEFAULT_EXPOSURE = '4.0'` - Default multiply value to get from raw linear to scene-linear.

`RT_DEFAULT_PROFILE = ''` - Path to the default RawTherapee pp3 preset to use. There is one included and set by default, but you can override this path if desired. There are similar variables for the other debayer engines that need config files as well.

## Debayer Engine Configuration
Here is some more information about how to configure custom debayer settings for each of the debayer engines. I've included quite a bit of extra information here about the decisions I've made and why. 

- [RawTherapee](docs/RawTherapee.md)
- [dcraw](dcraw.md)
- [DarkTable](Darktable.md)
- [vkdt](vkdt.md)

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

## Commandline Options
```
$ debayer -h
usage: debayer [-h] [-o OUTPUT] [-w] [-p PROFILE] [-en ENGINE] [-ca]
               [-r RESIZE] [-e EXPOSURE] [-j JOBS] [-f FILTER]
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
                        Optional override to specify a custom profile to use.
                        If none, the default config file will be used. Could
                        be a pp3 file for rawtherapee, xmp for darktable, or
                        cfg for vkdt.
  -en ENGINE, --engine ENGINE
                        Debayer engine to use: If none, the DEBAYER_ENGINE
                        variable in will be used. one of: 'rt', 'art', 'dc',
                        'dcrcd', 'dt', 'vkdt', 'oiio'
  -ca, --aberration     Remove chromatic aberration (rawtherapee or ART only)
  -r RESIZE, --resize RESIZE
                        Apply a resize to the output image. Aspect ratio is
                        not preserved if both width and height are specified.
                        <width>x<height> Or preserve aspect ratio if w or h =
                        0: e.g. "1920x0" Can also be a percentage like
                        "50%"(For Magic Lantern 1x3 anamorphic) 1920x2340 ->
                        5760x2340 -> 2880x1170 (ML 1x3 2.35) - 1808x2300 ->
                        (unsqueeze) 5424x2300 -> (0.5) 2712x1150 Or 1280x2160
                        (1x3) -> 3840x2160 -> 2560x1440 -> 1920x1080
  -e EXPOSURE, --exposure EXPOSURE
                        Raw to scene-linear exposure adjustment. Default is
                        4.0
  -j JOBS, --jobs JOBS  Number of simultaneous jobs.
  -f FILTER, --filter FILTER
                        Include only files that match regex. Can be comma
                        separated list.
```

## Exposure
One important parameter when debayering to scene-linear is how much to expose up with the `-e` parameter. Camera raw files are usually stored in an integer data format, which means the data is contained in a 0-1 container. How many bits of precision that data has within that container varies with the camera and sensor. 

To get this 0-1 data range into sensible scene-linear data, we need to expose up the raw data so that an 18% grey diffuse reflector will live at a scene-linear value of around 0.18. How much we need to expose up will of course depend on how the image was exposed in the camera. This also determines how much headroom you will have in highlights. A default value of 4.0 is provided as a starting point, but you will probably want to customize this depending on your source raw images.

## Custom Profile
You can specify a custom config file for your debayer engine with `-p path/to/file`. This is useful if you need to customize whitebalance or sharpening settings for example.

A default config is included in the repo for most debayer engines is used by default there is a -p switch enabled.

## Debayer Algorithms
If you are curious about the different available debayer algorithms in open software I have put together a big set of comparison images in jpg and exr available at this [mega.nz link](https://mega.nz/folder/ZEYg1bwL#jD1ED7P-D5srWdYR0PdP8A).

The images are processed with `dcraw_emu` for AHD, AAHD, DHT and VNG, and with `rawtherapee-cli` for RCD, DCB and AMaZE. The test images are a selection of 256x128 pixel crops of interesting image regions for judging debayer quality. My subjective ranking would be

```
RCD > DCB > AMaZE > DHT > AAHD > AHD > VNG
```

If you're curious, I wrote a [more in-depth discussion](docs/Debayer_Algorithms.md).

# Installation

## OpenImageIO
oiiotool can be installed with common pacakge managers on all platforms. [See this documentation](https://github.com/OpenImageIO/oiio/blob/master/INSTALL.md#installing-from-package-managers) for help.
## Rawtherapee
[Packages are provided](http://rawtherapee.com) for all platforms. However if you are on linux, the appimage won't give you access to the rawtherapee-cli commandline utility. You will need to install or compile it (or extract the contents of the appimage with ./Rawtherapee-5.8.Appimage --appimage-extract ). Note if you are on Centos 7, the Appimage will not work because it was compiled with a newer version of GLIBC. There is however a copr for many fedora and rhel distros including el7 [here](https://download.copr.fedorainfracloud.org/results/scx/rawtherapee/).  

IMPORTANT: For Rawtherapee 5.8 and below, you need to [install a custom icc output profile](docs/RawTherapee.md) in order to work around a [posterization bug](https://github.com/Beep6581/RawTherapee/issues/6378).

## LibRaw
[LibRaw provides](https://www.libraw.org/download) packages for Windows and Mac, and for Linux it is easy to compile with minimal dependencies. I would recommend compiling from [master](https://github.com/LibRaw/LibRaw) to get the latest raw formats like Canon CR3.
