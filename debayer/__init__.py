#!/usr/bin/env python
from __future__ import with_statement
from __future__ import print_function
from __future__ import division

import os
import sys
import argparse
import re
import tempfile
import shutil
import time
import datetime
import logging
import subprocess
import shlex
import pyseq
import distutils.spawn
import yaml


# Get config yaml file
dir_path = os.path.dirname(os.path.realpath(__file__))
CONFIG = os.path.join(dir_path, "config.yaml")

# Set up logger # %(levelname)s %(asctime)s
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    handlers=logging.StreamHandler(sys.stdout)
    )
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Debayer():
    '''
    Debayer is a class describing the conversion of a set of raw files into output images.

    Attributes:
        success (bool): True if everything is good to process images.
        image_sequences (list): List of tuples containing root dir and pyseq image sequence objects.
        autoexposure (float): auto exposure compensation.
        profile:
        possible_output_formats:
        output_formats:
        compression:
        datatypes:
        debayer_engine:
        colorspace_in:
        colorspaces_out:
        default_autoexposure:
        autoexposure_target:
        autoexposure_center_percentage:
        ocioconfig:
        resize_filter:
        default_format_resize:
        raw_formats:
    '''

    def __init__(self):

        # Create tmp directory on local disk
        self.tmp_dir = tempfile.mkdtemp()
        log.debug("Temp Directory is {0}".format(self.tmp_dir))

        self.success = self.validate()

        if self.success:
            self.process()

        # Remove temp directory
        if self.tmp_dir:
            try:
                shutil.rmtree(self.tmp_dir)
            except WindowsError as error:
                log.error(error)

    def validate(self):
        '''
        Validate everything necessary to begin work:
            - Gather settings from the config file
            - Gather commandline arguments
            - Verify everything we need exists
            - Gather all inpput images
        '''

        # Set up logger and gather input variables
        self.image_sequences = []
        self.autoexposure = 1.0

        # Get Config file data
        if os.path.isfile(CONFIG):
            with open(CONFIG, 'r') as configfile:
                self.config = yaml.load(configfile)
        else:
            log.error("Error: Could not find config file {0}".format(CONFIG))
            return None

        # Config Options

        # Get locations of executables
        for exe, location in self.config.get('executable_locations').iteritems():
            if exe == "rawtherapee_cli":
                if exe.startswith(os.path.sep):
                    self.rawtherapee_cli = location
                else:
                    self.rawtherapee_cli = distutils.spawn.find_executable(
                        location)
                if not self.rawtherapee_cli or not os.path.exists(self.rawtherapee_cli):
                    msg = 'rawtherapee-cli executable count not be found in "{}".'
                    log.error(msg.format(self.rawtherapee_cli))
                    self.rawtherapee_cli = None
                    return None

            elif exe == "dcraw":
                if exe.startswith(os.path.sep):
                    self.dcraw = location
                else:
                    self.dcraw = distutils.spawn.find_executable(location)
                if not self.dcraw or not os.path.exists(self.dcraw):
                    msg = 'dcraw executable count not be found in "{}".'
                    log.error(msg.format(self.dcraw))
                    self.dcraw = None

            elif exe == "oiiotool":
                if exe.startswith(os.path.sep):
                    self.oiiotool = location
                else:
                    self.oiiotool = distutils.spawn.find_executable(location)
                if not self.oiiotool or not os.path.exists(self.oiiotool):
                    msg = 'oiiotool executable count not be found in "{}".'
                    log.error(msg.format(self.oiiotool))
                    self.oiiotool = None
                    return None

            elif exe == 'exiftool':
                if exe.startswith(os.path.sep):
                    self.exiftool = location
                else:
                    self.exiftool = distutils.spawn.find_executable(location)
                if not self.exiftool or not os.path.exists(self.exiftool):
                    # If no exiftool, we'll just skip tif metadata copying.
                    msg = 'exiftool executable count not be found in "{}". No metadata will be copied to tif files.'
                    log.error(msg.format(self.exiftool))
                    self.exiftool = None

        self.profile = self.config.get('rt_default_profile')
        possible_output_formats = self.config.get('possible_output_formats')
        self.output_formats = self.config.get('default_output_formats')
        self.compression = self.config.get('compression')
        self.datatypes = self.config.get('datatype')
        self.debayer_engine = self.config.get('debayer_engine')
        self.colorspace_in = self.config.get('colorspace_in')
        self.colorspaces_out = self.config.get('colorspaces_out')
        self.default_autoexposure = self.config.get('autoexpose')
        self.autoexposure_target = self.config.get('autoexposure_target')
        self.autoexposure_center_percentage = self.config.get(
            'autoexposure_center_percentage')
        self.ocioconfig = self.config.get('default_ocioconfig') or ''
        self.resize_filter = self.config.get('resize_filter')
        self.default_format_resize = self.config.get('default_format_resize')

        self.raw_formats = self.config.get('raw_formats')
        self.raw_formats = self.raw_formats + \
            [r.upper() for r in self.raw_formats]

        log.debug("Processing raw formats:\n" + " ".join(self.raw_formats))

        # Get commandline arguments
        parser = argparse.ArgumentParser(
                            description="Debayer raw files to output images. For each of one or more input directories,\n"
                                        "recursively find all raw files, recreate the directory structure, and convert to output images in destination directory")

        parser.add_argument("-v", "--verbose",
                            action="store_true",
                            help="Output lots of useless information.",
                            required=False)

        parser.add_argument("input_paths",
                            help="Source(s) to process. Can one or more directories or raw images.",
                            type=str,
                            action='store',
                            nargs='+')

        parser.add_argument("-o", "--output",
                            help="Output directory. If not specified, the current directory will be used.",
                            required=False)

        parser.add_argument("-w", "--overwrite",
                            action="store_true",
                            help="Overwrite existing output files.",
                            required=False)

        parser.add_argument("-f", "--output_formats",
                            help="Output image format. Default is exr.\n"
                                 "This can be exr, tif, jpg. Or a comma separated list like \"exr,jpg\"",
                            required=False)

        parser.add_argument("-p", "--profile",
                            help="Optional override to specify a custom rawtherapee pp3 profile to use.\n"
                                 "If none, the default in the config file will be used.",
                            required=False)

        parser.add_argument("-ca", "--aberration",
                            help="Remove chromatic aberration (rawtherapee only)\n",
                            action="store_true",
                            required=False)

        parser.add_argument("--ocioconfig",
                            help="OCIO config to use. If none specified, a generic ACES config will be used, which should handle most common color transforms.",
                            required=False)

        parser.add_argument("-c", "--colorspaces_out",
                            help="Output OCIO colorspace. If not specified the default defined in the config will be used.\n"
                                 "format: <format>:<colorspace> - e.g. \"exr:lin_ap1,tif:lin_ap1,jpg:out_rec709\" or \n"
                                 "\"exr:lin_sgamut3cine\" or \"ACES - ACEScg\"",
                            required=False)

        parser.add_argument("-r", "--resize",
                            help="Apply a resize to the output image. Aspect ratio is not preserved if both width and height are specified.\n"
                                 "<width>x<height>. 1920x2348 (1x3) -> 5760x2348 -> 3840x1565 -> 2880x1174.\n"
                                 "Or 1280x2160 (1x3) -> 3840x2160 -> 2560x1440 -> 1920x1080.\n"
                                 "Or preserve aspect ratio if w or h = 0: e.g. \"1920x0\"\n"
                                 "Can also be a percentage like \"50%%\"",
                            required=False)

        parser.add_argument("-e", "--exposure",
                            type=float,
                            help="Exposure adjust the output image. No autoexposure will be performed. e.g. 1.1 1.5 2.0",
                            required=False)

        parser.add_argument("-a", "--autoexpose",
                            action="store_true",
                            help="Auto expose. Image sequences will have static exposure adjustement.",
                            required=False)

        parser.add_argument("-ae", "--autoexpose_each",
                            action="store_true",
                            help="Auto expose each frame.",
                            required=False)

        parser.add_argument("-se", "--search_exclude",
                            help="Strings to ignore. If image full path contains string, skip.\n"
                                 "Can be comma separated list.",
                            required=False)

        parser.add_argument("-si", "--search_include",
                            help="Only include files that contain <search_include>.\n"
                                 "Can be comma separated list.",
                            required=False)

        # Show help if no args.
        if len(sys.argv) == 1:
            parser.print_help()
            return None

        args = parser.parse_args()

        if args.verbose:
            log.setLevel(logging.DEBUG)

        input_dirs = []
        if args.input_paths:
            for input_path in args.input_paths:
                # Support ~ and relative paths
                input_path = os.path.expanduser(input_path)
                input_path = os.path.realpath(input_path)
                if os.path.isdir(input_path):
                    input_dirs.append(input_path)
                elif os.path.isfile(input_path):
                    # Directly add all raw images found to image_sequences list
                    if "." in input_path:
                        input_path_ext = input_path.split('.')[-1]
                    if input_path_ext in self.raw_formats:
                        self.image_sequences.append(
                            (os.path.dirname(input_path), pyseq.Sequence([input_path])))
        if args.output:
            self.dst = args.output
            self.dst = os.path.expanduser(self.dst)
            self.dst = os.path.realpath(self.dst)
            if not os.path.isdir(self.dst):
                os.makedirs(self.dst)

        else:
            self.dst = os.getcwd()

        # RawTherapee Profile
        if args.profile:
            self.profile = args.profile
        else:
            # Allow relative pathing in config
            if not self.profile.startswith(os.path.sep):
                self.profile = os.path.join(dir_path, self.profile)
        if self.profile:
            self.profile = os.path.expanduser(self.profile)
            self.profile = os.path.realpath(self.profile)
        if not os.path.isfile(self.profile):
            log.error("Error: Specified profile does not exist.")
            return None

        self.aberration = args.aberration
        if self.aberration:
            # Copy pp3 profile to temp dir
            tmp_profile = os.path.join(
                self.tmp_dir, os.path.basename(self.profile))
            log.debug("Chromatic Aberration specified: Creating temp profile: {0}".format(
                tmp_profile))
            shutil.copyfile(self.profile, tmp_profile)
            cmd = ['sed', '-i', '-e', "'s/CA=false/CA=true/'", tmp_profile]
            log.debug(' '.join(cmd))
            sed_proc = subprocess.Popen(cmd)
            result, error = sed_proc.communicate()
            if not error:
                self.profile = tmp_profile

        self.resize = args.resize

        self.autoexpose = args.autoexpose
        self.autoexpose_each = args.autoexpose_each

        self.exposure = args.exposure
        # No autoexposure if args.exposure is specified
        if self.exposure:
            self.autoexpose_each = None
            self.autoexpose = None

        # Default autoexposure if none specified
        if not self.autoexpose and not self.autoexpose_each:
            if self.default_autoexposure != "none":
                if self.default_autoexposure == "a":
                    self.autoexpose = True
                elif self.default_autoexposure == "ae":
                    self.autoexpose_each = True

        # Ignore string
        self.search_exclude = args.search_exclude
        if self.search_exclude:
            if "," in self.search_exclude:
                self.search_exclude_list = [
                    i.strip() for i in self.search_exclude.rsplit(',')]
            else:
                self.search_exclude_list = [self.search_exclude.strip()]
        else:
            self.search_exclude_list = None

        # Search filter String
        self.search_include = args.search_include
        if self.search_include:
            if "," in self.search_include:
                self.search_include_list = [
                    i.strip() for i in self.search_include.rsplit(',')]
            else:
                self.search_include_list = [self.search_include.strip()]
        else:
            self.search_include_list = None

        self.overwrite = args.overwrite

        # Output Format
        if args.output_formats:
            self.output_formats = []
            output_formats_string = args.output_formats
            if "," in output_formats_string:
                for output_format in output_formats_string.split(','):
                    if output_format in possible_output_formats:
                        self.output_formats.append(output_format)
            else:
                # Assume it's just one format
                if output_formats_string in possible_output_formats:
                    self.output_formats.append(output_formats_string)
            if not self.output_formats:
                log.error('Error: Invalid output format specified')
                return None

        # OCIO Config Setup
        if args.ocioconfig:
            self.ocioconfig = args.ocioconfig
            self.ocioconfig = os.path.realpath(self.ocioconfig)
            self.ocioconfig = os.path.expanduser(self.ocioconfig)
            if not os.path.isfile(self.ocioconfig):
                log.error('Error: Specified OCIO Config does not exist')
                self.ocioconfig = ''
        if not self.ocioconfig:
            env_ocio = os.getenv("OCIO")
            if env_ocio:
                self.ocioconfig = env_ocio
        if not os.path.exists(self.ocioconfig):
            log.warning('OCIO Config does not exist: \n\t{0}\n\tNo OCIO color transform will be applied'.format(
                self.ocioconfig))
            self.ocioconfig = None
        log.debug('OCIO Config: {0}'.format(self.ocioconfig))

        # OCIO Colorspace for output image
        if args.colorspaces_out:
            self.colorspaces_out = {}
            if "," in args.colorspaces_out:
                entries = args.colorspaces_out.split(',')
            else:
                entries = [args.colorspaces_out]
            for entry in entries:
                if ":" in entry:
                    output_format, colorspace = entry.split(':')
                    self.colorspaces_out[output_format] = colorspace
                else:
                    # If no image format specified, assume exr
                    self.colorspaces_out['exr'] = args.colorspaces_out
            log.debug("Output Color Transform: {0}".format(
                self.colorspaces_out))

        # Find source raw images
        for input_dir in input_dirs:
            self.gather_images(input_dir)

        if self.image_sequences:
            log.debug("Found these image sequences:\n" +
                      "\n".join([img[1].path() for img in self.image_sequences]))
            return True
        else:
            log.error('Found no image sequences... Please try again')
            return False

    def process(self):
        '''
        Convert every raw image in image_sequences into the output format(s).
        '''

        # Loop through all found image sequences to process
        for root_dir, sequence in self.image_sequences:
            if len(sequence) > 2:
                log.info("Debayering image sequence:\n\t{0}".format(
                    os.path.join(sequence.dirname, sequence.format('%h%p%t %r'))))

            # Create destination directories if they don't exist
            dst_dir = self.dstconv(sequence.dirname, root_dir)
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)

            if self.autoexpose:
                # Get autoexposure from middle frame
                middle_frame = sequence[int(sequence.length() / 2)]
                if not self.autoexpose_each:
                    # temp debayer for auto exposure
                    output_image_path = self.dstconv(
                        middle_frame.path, root_dir)
                    output_image_path = os.path.splitext(output_image_path)[0]
                    tmp_output_image = self.debayer_image(
                        middle_frame.path, output_image_path)
                    if tmp_output_image:
                        self.autoexposure = self.calc_autoexposure(
                            tmp_output_image)
                        log.info("Auto exposure:\n\t{0} calculated from middle frame: {1}".format(
                            self.autoexposure, os.path.basename(middle_frame))
                            )
                        os.remove(tmp_output_image)
                    else:
                        log.error(
                            "Error: Could not calc autoexposure. Setting to 1.0")
                        self.autoexposure = 1.0
            else:
                self.autoexposure = 1.0

            # Loop through all images in sequence
            for image in sequence:
                start_time = time.time()

                output_image_path = self.dstconv(image.path, root_dir)
                output_image_path = os.path.splitext(output_image_path)[0]
                log.info("\nsrc: \t{0}".format(image.path))

                # Debayer image to temp tif file
                tmp_output_image = self.debayer_image(
                    image.path, output_image_path)
                if tmp_output_image:
                    for output_format in self.output_formats:
                        output_image = self.convert_image(
                            tmp_output_image, output_image_path, output_format=output_format)
                        log.info("dst:\t{0}".format(output_image))
                    elapsed_time = datetime.timedelta(
                        seconds=time.time() - start_time)
                    log.info("time: \t{0}".format(elapsed_time))
                    # Clean up file
                    os.remove(tmp_output_image)

    def dstconv(self, src_path, toplevel_dir, dst_path=None):
        '''
        Convert src_path to dstpath, reconstructing path under rootpath in dstpath.
        :param src_path: source path to convert.
        :param toplevel_dir: directory to split src_path in order to generate destination path.
        :param dst_path: optional destination path override. Otherwise class attrib dst will be used.
        '''
        if not dst_path:
            dst_path = self.dst
        return dst_path + src_path.split(toplevel_dir)[-1]

    def gather_images(self, source_dir):
        '''
        Gather all image sequences found in source dir and add to self.image_sequences.
        Args:
            source_dir: The directory path to process.
        '''
        generator = pyseq.walk(source_dir, -1)
        if generator:
            for path, parentdir, sequences in generator:
                for sequence in sequences:
                    file_extension = os.path.splitext(
                        sequence.path())[1][1:].strip()
                    if file_extension in self.raw_formats:
                        self.image_sequences.append((source_dir, sequence))

    def debayer_image(self, input_image, output_image_path, retry=0):
        '''
        Debayer the given input image into a scene-linear float tiff file
        :param input_image: (str) Input path of image to debayer.
        :param output_image_path: (str) path of output image without file extension
        :param retry: (int) retry level to control recursion.
        '''

        # Skip existing output image files unless self.overwrite is enabled
        if not self.overwrite:
            for image_format in self.output_formats:
                final_output_image = output_image_path + \
                    ".{0}".format(image_format)
                if os.path.exists(final_output_image) and self.get_size(final_output_image)[0] > 0.01:
                    log.warning("skip existing:\t{0}".format(
                        final_output_image))
                    return None
        # Skip files in ignore_list
        if self.search_exclude_list:
            for ignore_item in self.search_exclude_list:
                if ignore_item in input_image:
                    log.warning("exlude ignore:\t{0}".format(input_image))
                    return None
        # Only process files in filter list
        if self.search_include_list:
            for include_item in self.search_include_list:
                if include_item not in input_image:
                    log.warning("exluded:\t{0}".format(input_image))
                    return None

        tmp_output_image = os.path.join(
            self.tmp_dir, os.path.basename(output_image_path)) + ".tif"

        log.debug("tmp:\t{0}".format(tmp_output_image))

        if self.debayer_engine == "dcraw":
            if not self.dcraw:
                log.error("Error: dcraw executable not found. Exiting...")
                return None

            # dcraw tutorial: http://www.guillermoluijk.com/tutorial/dcraw/index_en.htm
            # rawpy might be another option https://letmaik.github.io/rawpy/api/rawpy.Params.html#rawpy.Params
            dcraw_cmd = ['dcraw', '-v', '-T', '-4', '-o', '6',
                         '-q', '3', '-w', '-H', '0', '-W', '-c', input_image]

            with open(tmp_output_image, "w") as output_file:
                log.debug(' '.join(dcraw_cmd))
                dcraw_proc = subprocess.Popen(
                    dcraw_cmd,
                    stdout=output_file
                    )
            result, error = dcraw_proc.communicate()
            if error:
                log.error("Error Processing Result: " + error)
            if not os.path.isfile(tmp_output_image):
                if retry < 3:
                    self.debayer_image(
                        input_image, output_image_path, retry=retry+1)
            else:
                self.copy_metadata(input_image, tmp_output_image)
                return tmp_output_image

        elif self.debayer_engine == "rt":
            rtcli_cmd = [
                self.rawtherapee_cli, '-o', tmp_output_image, '-p',
                self.profile, '-b16f', '-Y', '-q', '-f', '-t', '-c', input_image,
            ]
            log.debug(' '.join(rtcli_cmd))
            rtcli_proc = subprocess.Popen(
                rtcli_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
                )
            result, error = rtcli_proc.communicate()
            if error:
                log.error("Error Processing Result: " + error)
            if not os.path.isfile(tmp_output_image):
                log.warning(
                    "Output file did not generate:\n\t{0}".format(tmp_output_image))
                if retry < 1:
                    self.debayer_image(
                        input_image, output_image_path, retry=retry+1)
            else:
                output_size, output_size_str = self.get_size(tmp_output_image)
                log.debug("Output size is: {0}".format(output_size_str))
                if output_size > 0.01:
                    return tmp_output_image
                else:
                    log.warning(
                        "File size of output is less than 4kb, processing again...")
                    os.remove(tmp_output_image)
                    if retry < 1:
                        self.debayer_image(
                            input_image, output_image_path, retry=retry+1)

    def convert_image(self, src_img, dst_img, output_format="exr"):
        ''' Convert src_img to specified format at dst_img
            Args:
                src_img: (str) Source path of raw image to convert.
                dst_img: (str) Destination path of image to output, with file extension removed.
                output_formats: (str) Output image format to convert to.
        '''
        # calculate new autoexposure for each frame if self.autoexpose_each
        if self.autoexpose_each:
            self.autoexposure = self.calc_autoexposure(src_img)
            log.info("autoexposure {0} for {1}".format(
                self.autoexposure, os.path.basename(src_img)))

        dst_img = dst_img + ".{0}".format(output_format)
        oiiotool_cmd = [self.oiiotool, '-v', src_img]

        # Setup resize string
        resize_list = ['--rangecompress']
        if self.resize_filter:
            resize_list.append('--resize:filter={}'.format(self.resize_filter))
        else:
            resize_list.append('--resize')

        current_format_resize = self.default_format_resize[output_format]
        if current_format_resize:
            resize = current_format_resize
        else:
            resize = self.resize
        resize_list += [resize, '--rangeexpand']

        if resize:
            oiiotool_cmd += resize_list

        # Specify datatype
        if output_format in self.datatypes:
            if self.datatypes[output_format] in ["uint8", "sint8", "uint10", "uint12", "uint16", "sint16", "uint32", "sint32", "half", "float", "double"]:
                oiiotool_cmd += ['-d', self.datatypes[output_format]]

        if self.autoexposure != 1.0:
            exp = str(self.autoexposure)
            exp = [exp, exp, exp, '1.0']
            oiiotool_cmd += ['--mulc', ','.join(exp)]
        if self.exposure:
            exp = str(self.exposure)
            exp = [exp, exp, exp, '1.0']
            oiiotool_cmd += ['--mulc', ','.join(exp)]

        # Validate OCIO stuff
        if self.colorspaces_out:
            if output_format in self.colorspaces_out:
                if self.ocioconfig:
                    oiiotool_cmd += [
                        '--colorconfig',
                        self.ocioconfig,
                        '--colorconvert',
                        self.colorspace_in,
                        self.colorspaces_out[output_format],
                    ]

        # Output format compression options
        if self.compression:
            if output_format in self.compression:
                oiiotool_cmd += self.compression[output_format]

        # Output image
        oiiotool_cmd += ['-o', dst_img]
        log.debug(' '.join(oiiotool_cmd))
        oiiotool_proc = subprocess.Popen(
            oiiotool_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        result, error = oiiotool_proc.communicate()

        if os.path.isfile(dst_img):
            # Copy metadata for tif output
            if output_format == "tif":
                self.copy_metadata(src_img, dst_img)
            return dst_img
        else:
            log.error(
                "Output {0} file did not generate!".format(output_format))
            return None

    def calc_autoexposure(self, imgpath):
        '''
        Calculate an autoexposure value based on an average pixel sample.
        :param imgpath: (str) path of image to sample.
        '''
        try:
            import OpenImageIO as oiio
        except ImportError:
            log.error(
                "Missing dependencies. Please install OpenImageIO to enable autoexposure. Using default exposure of 1.0")
            return 1.0
        # Create ImageBuf from ImageInput
        imgbuf = oiio.ImageBuf(imgpath)
        imgspec = imgbuf.spec()

        # Construct ROI from self.autoexposure_center_percentage
        center = (int(imgspec.width/2), int(imgspec.height/2))
        size = (int(imgspec.width * self.autoexposure_center_percentage),
                int(imgspec.height * self.autoexposure_center_percentage))

        box_roi = oiio.ROI(int(center[0]-size[0]/2), int(center[0]+size[0]/2),
                           int(center[1]-size[1]/2), int(center[1]+size[1]/2))
        pixels = imgbuf.get_pixels(format=oiio.FLOAT, roi=box_roi)
        img_average = pixels.mean()
        return self.autoexposure_target / img_average

    def copy_metadata(self, src, dst):
        '''Uses exiftool to copy all metadata from src image path to dst image path
        Args:
            src {str} -- image path of source image
            dst {str} -- image path of destination
        '''
        if self.exiftool:
            exiftool_cmd = [self.exiftool,
                            '-overwrite_original', '-tagsFromFile', src, dst]
            log.debug('Copying exif metadata from raw')
            log.debug(' '.join(exiftool_cmd))
            exiftool_proc = subprocess.Popen(exiftool_cmd)
            result, error = exiftool_proc.communicate()
            if error:
                log.warning("Copying metadata failed: {0}".format(error))
                return None
            else:
                return True
        else:
            log.error("Error: exiftool not found. Will skip setting the metadata")
            return None

    def get_size(self, filepath, suffix='B'):
        ''' Return filesize of filepath '''
        num = os.path.getsize(filepath)
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return num, "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return num, "%.1f%s%s" % (num, 'Yi', suffix)


if __name__ == "__main__":
    Debayer()
