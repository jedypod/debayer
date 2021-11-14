# dcraw_emu Configuration
Here is a little guide on how to use the `dcraw_emu` commandline utility that is included with [LibRaw](https://github.com/LibRaw/LibRaw).

Here are the complete commandline parameters:
```
dcraw_emu: almost complete dcraw emulator
Usage:  dcraw_emu [OPTION]... [FILE]...
-c float-num       Set adjust maximum threshold (default 0.75)
-v        Verbose: print progress messages (repeated -v will add verbosity)
-w        Use camera white balance, if possible
-a        Average the whole image for white balance
-A <x y w h> Average a grey box for white balance
-r <r g b g> Set custom white balance
+M/-M     Use/don't use an embedded color matrix
-C <r b>  Correct chromatic aberration
-P <file> Fix the dead pixels listed in this file
-K <file> Subtract dark frame (16-bit raw PGM)
-k <num>  Set the darkness level
-S <num>  Set the saturation level
-R <num>  Set raw processing options to num
-n <num>  Set threshold for wavelet denoising
-H [0-9]  Highlight mode (0=clip, 1=unclip, 2=blend, 3+=rebuild)
-t [0-7]  Flip image (0=none, 3=180, 5=90CCW, 6=90CW)
-o [0-8]  Output colorspace (raw,sRGB,Adobe,Wide,ProPhoto,XYZ,ACES,
          DCI-P3,Rec2020)
-o file   Output ICC profile
-p file   Camera input profile (use 'embed' for embedded profile)
-j        Don't stretch or rotate raw pixels
-W        Don't automatically brighten the image
-b <num>  Adjust brightness (default = 1.0)
-q N      Set the interpolation quality:
          0 - linear, 1 - VNG, 2 - PPG, 3 - AHD, 4 - DCB
          11 - DHT, 12 - AAHD
-h        Half-size color image (twice as fast as "-q 0")
-f        Interpolate RGGB as four colors
-m <num>  Apply a 3x3 median filter to R-G and B-G
-s [0..N-1] Select one raw image from input file
-4        Linear 16-bit, same as "-6 -W -g 1 1
-6        Write 16-bit output
-g pow ts Set gamma curve to gamma pow and toe slope ts (default = 2.222 4.5)
-T        Write TIFF instead of PPM
-G        Use green_matching() filter
-B <x y w h> use cropbox
-F        Use FILE I/O instead of streambuf API
-Z <suf>  Output filename generation rules
          .suf => append .suf to input name, keeping existing suffix too
           suf => replace input filename last extension
          - => output to stdout
          filename.suf => output to filename.suf
-timing   Detailed timing report
-fbdd N   0 - disable FBDD noise reduction (default), 1 - light FBDD, 2 - full
-dcbi N   Number of extra DCD iterations (default - 0)
-dcbe     DCB color enhance
-aexpo <e p> exposure correction
-apentax4shot enables merge of 4-shot pentax files
-apentax4shotorder 3102 sets pentax 4-shot alignment order
-mmap     Use memory mmaped buffer instead of plain FILE I/O
-mem       Use memory buffer instead of FILE I/O
-disars   Do not use RawSpeed library
-disinterp Do not run interpolation step
-dsrawrgb1 Disable YCbCr to RGB conversion for sRAW (Cb/Cr interpolation enabled)
-dsrawrgb2 Disable YCbCr to RGB conversion for sRAW (Cb/Cr interpolation disabled)
-doutputflags N set params.output_flags to N
```

By default, [debayer](https://github.com/jedypod/debayer) will use the following options:

`dcraw_emu -4 -T -q 4 -dcbe -o 5 -H 2 -Z - output_image.tif`

- `-4` : This outputs linear 16 bit integer data.
- `-T` : We need this to output a tif file instead of PPM
- `-q 4 -dcbe` : This sets the demoisaic algorithm. dcraw_emu includes more options than the original dcraw, but does not include as many as Rawtherapee or Darktable. The best options, (in order) are `DCB (with -dcbe)` > `AAHD` > `DHT`. Each has its pros and cons. See [Debayer Algorithms](Debayer_Algorithms.md) for more in-depth info.
- `-o 5` : This sets the output colorspace. Here was use XYZ output, and convert to ACEScg during conversion to exr in oiiotool.
- `-H 2` : This sets the highlight reconstruction mode to "blend". This automatically exposes down the output image by 1 stop, but does not change linearity. This mode is pretty much equivalent to the "Luminance Recovery" mode in RawTherapee.
- `-Z -` : This switch is necessary so that we can manually specify the output image name.