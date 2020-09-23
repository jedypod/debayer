# Debayer

## Description
Debayer is a commandline tool to process camera raw image formats into scene-linear exr and other formats. It uses OpenImageIO oiiotool with OpenColorIO, RawTherapee, DCRaw and exiftool.

## Overview
Debayer is a commandline tool designed to debayer raw files into scene-linear ACES exr. It also supports other output colorspaces using OpenColorIO, and supports tif, jpeg, or exr output formats.

There is a yaml config file where you specify configuration options such as the locations of the required executables, exr compression settings, and default colorspace transforms.

## Usage
The only argument required to run debayer is a source directory. Debayer runs recursively on the source directory: all raw files inside the source directory and all subdirectories will be debayered. The source directory tree will be reconstructed under the destination directory.

Debayer works by using either RawTherapee or dcraw to debayer the source raw file to a temporary tiff file. The temporary tiff file will be an ACES 2065-1 colorspace scene-linear image. This image is then used as a source for openimageio to convert to whatever the output format and colorspace is.

Debayer uses a "default" pp3 profile when using rawtherapee, which will output to scene-linear ACES 2065-1 32 bit float tiff (assuming the defaults in the config are kept).

A common workflow would be to open rawtherapee and set up a profile on an example image. For example, to whitebalance accurately, to set up chromatic abberration and defringing, or specify custom sharpening or debayer algorithm settings. Once you have a pp3 profile, you can save this in your output directory, and specify it with the `-p` flag.

Debayer can also auto-expose your raw images with a crude autoexposure algorithm with the `-a` flag. The default behavior is to autoexpose once on the center frame for image sequences, but you can autoexpose each frame if desired with the `-ae` flag. The autoexposure_center_percentage and autoexposure_target values in the config file will determine the calculated autoexposure.

## Commandline Options
    usage: debayer [-h] [-v] [-o OUTPUT] [-w] [-f OUTPUT_FORMATS] [-p PROFILE]
                [-ca] [--ocioconfig OCIOCONFIG] [-c COLORSPACES_OUT]
                [-r RESIZE] [-e EXPOSURE] [-a] [-ae] [-se SEARCH_EXCLUDE]
                [-si SEARCH_INCLUDE]
                input_paths [input_paths ...]

    Debayer raw files to output images. For each of one or more input directories,
    recursively find all raw files, recreate the directory structure, and convert
    to output images in destination directory

    positional arguments:
    input_paths           Source(s) to process. Can one or more directories or
                            raw images.

    optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         Output lots of useless information.
    -o OUTPUT, --output OUTPUT
                            Output directory. If not specified, the current
                            directory will be used.
    -w, --overwrite       Overwrite existing output files.
    -f OUTPUT_FORMATS, --output_formats OUTPUT_FORMATS
                            Output image format. Default is exr. This can be exr,
                            tif, jpg. Or a comma separated list like "exr,jpg"
    -p PROFILE, --profile PROFILE
                            Optional override to specify a custom rawtherapee pp3
                            profile to use. If none, the default in the config
                            file will be used.
    -ca, --aberration     Remove chromatic aberration (rawtherapee only)
    --ocioconfig OCIOCONFIG
                            OCIO config to use. If none specified, a generic ACES
                            config will be used, which should handle most common
                            color transforms.
    -c COLORSPACES_OUT, --colorspaces_out COLORSPACES_OUT
                            Output OCIO colorspace. If not specified the default
                            defined in the config will be used. format:
                            <format>:<colorspace> - e.g.
                            "exr:lin_ap1,tif:lin_ap1,jpg:out_rec709" or
                            "exr:lin_sgamut3cine" or "ACES - ACEScg"
    -r RESIZE, --resize RESIZE
                            Apply a resize to the output image. Aspect ratio is
                            not preserved if both width and height are specified.
                            <width>x<height>. 1920x2348 (1x3) -> 5760x2348 ->
                            3840x1565 -> 2880x1174. Or 1280x2160 (1x3) ->
                            3840x2160 -> 2560x1440 -> 1920x1080. Or preserve
                            aspect ratio if w or h = 0: e.g. "1920x0" Can also be
                            a percentage like "50%"
    -e EXPOSURE, --exposure EXPOSURE
                            Exposure adjust the output image. No autoexposure will
                            be performed. e.g. 1.1 1.5 2.0
    -a, --autoexpose      Auto expose. Image sequences will have static exposure
                            adjustement.
    -ae, --autoexpose_each
                            Auto expose each frame.
    -se SEARCH_EXCLUDE, --search_exclude SEARCH_EXCLUDE
                            Strings to ignore. If image full path contains string,
                            skip. Can be comma separated list.
    -si SEARCH_INCLUDE, --search_include SEARCH_INCLUDE
                            Only include files that contain <search_include>. Can
                            be comma separated list.


## Dependencies
- [OpenImageIO](https://github.com/OpenImageIO/oiio) - Python module is used for autoexposure calculation. oiiotool is used for exr conversion after debayer.
- [RawTherapee](https://rawtherapee.com/downloads) - Used for raw file debayering: Preferred high quality option. Supports more colorspaces and has better demoiseaicing algorithms.
- [dcraw](https://www.cybercom.net/~dcoffin/dcraw/) - Used for raw file debayering: simple option. Limited to AHD demoisaicing and has limited raw file processing options.
- [exiftool](https://www.sno.phy.queensu.ca/~phil/exiftool/) - Used for copying metadata to tif output images, and when using dcraw.
- [PyYAML](https://pyyaml.org/wiki/PyYAML) - Used to read the yaml configuration file.

## Installation
### OSX
On OSX, [Homebrew](https://brew.sh) can easily be used to install the needed dependencies:

`brew install openimageio dcraw python pip exiftool`

Pip can be used to install the python dependencies needed:

`pip install debayer`

### Linux
On Fedora Linux, most dependencies can be installed with the package manager.

`dnf install python rawtherapee pip openimageio dcraw exiftool`

`pip install debayer`

For other distributions I'm assuming it would be pretty straightforward as well...

### Windows
On Windows you will have to download and install [Python](https://www.python.org/downloads). Make sure to you check the option to "Add Python to PATH".

Install [ImageMagick](https://imagemagick.org/script/download.php#windows) and make sure the "Add application to your system path" option is checked.

You will also have to install [RawTherapee](https://rawtherapee.com) and [ExifTool](https://exiftool.org). Make sure to edit your Windows environment variables to point to the folders holding these binaries.

Debayer can be then installed using PyPi.

`pip install debayer`

## The MIT License
Copyright 2019 Jedediah Smith

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.