#!/usr/bin/python3
"""
Helpful posts and articles:
* https://superuser.com/a/556031
* http://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html
* https://superuser.com/a/1275521/18382
* https://stackoverflow.com/a/34338901/177663

* The giftool that keeps on giffing!
* Keep calm and gif on!
"""
import logging
import math
import os
import shlex
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from concurrent.futures import ThreadPoolExecutor
from os.path import basename, splitext, isfile, exists, getsize, expanduser
from subprocess import CalledProcessError, check_call


log = logging.getLogger('vigif')


def pretty_size(value):
    """Convert a number of bytes into a human-readable string, with 4 significant digits.
    Output is 2...5 characters. Values >= 1000 always produce output in form: x.xxxU, xx.xxU, xxxU, xxxxU.
    """
    exp = int(math.log(value, 1024)) if value > 0 else 0
    unit = 'bkMGTPEZY'[exp]
    if exp == 0:
        return '%d%s' % (value, unit)       # value < 1024, result is always without fractions

    unit_value = value / (1024.0 ** exp)    # value in the relevant units
    places = int(math.log(unit_value, 10))  # number of digits before decimal point
    return '%.*f%s' % (2 - places, unit_value, unit)


def escape_shell_command(cmd_args: list):
    """Escape a shell command (list of strings). This is ONLY used for logging/debugging."""
    return ' '.join(shlex.quote(arg) for arg in cmd_args)


def call_command(cmd_args: list):
    log.debug("Running: %s", escape_shell_command(cmd_args))
    return check_call(cmd_args)


preset = {}


def convert_inner(path):
    filename = basename(path)
    out_path = splitext(filename)[0] + '.gif'

    if not exists(path):
        log.error("Does not exist: %s" % path)
        return

    if path.endswith('.gif') or not isfile(path):
        log.warning("Skipping gif: %s" % filename)
        return

    if exists(out_path):
        log.warning("WARN: Overwriting %s" % out_path)

    # FFmpeg loglevel 24 = warning, 16 = error
    cmd = 'ffmpeg', '-y', '-loglevel', ('24' if preset['verbosity'] >= 0 else '16')

    # Cut ####
    if preset['start']:
        cmd += '-ss', str(preset['start'])
    if preset['length']:
        cmd += '-t', str(preset['length'])

    # Conversion ####
    conversion = []

    if preset['slower'] or preset['faster']:
        ratio = 1 + (preset['slower'] if 'slower' in preset else -preset['faster'])/100
        conversion.append('setpts={}*PTS'.format(ratio))
    if preset['fps']:
        conversion.append('fps={fps}'.format(**preset))
    if preset['crop_left'] or preset['crop_right'] or preset['crop_top'] or preset['crop_bottom']:
        conversion.append('crop=in_w*{}:in_h*{}:in_w*{}:in_h*{}'
                          .format(1 - (preset['crop_left'] + preset['crop_right'])/100,
                                  1 - (preset['crop_top'] + preset['crop_bottom'])/100,
                                  preset['crop_left']/100,
                                  preset['crop_top']/100))
    if preset['scale']:
        # Doc: https://trac.ffmpeg.org/wiki/Scaling
        conversion.append('scale=min(iw\\,{scale}):min(ih\\,{scale}):'
                          'force_original_aspect_ratio=decrease:flags=lanczos'
                          .format(**preset))

    if preset['ppdenoise']:
        # https://ffmpeg.org/ffmpeg-filters.html#pp
        # The defaults are too aggressive, causing annoying artifacts. 1|1|1 seems to work well
        conversion.append('pp=tmpnoise|1|1|1')

    if preset['atadenoise']:
        # https://ffmpeg.org/ffmpeg-filters.html#toc-atadenoise
        # The defaults are quite good, attempting to "hand-tune" usually makes it worse
        conversion.append('atadenoise')

    # There's also owdenoise but it's extremely slow and not very good

    # Palettegen ####
    # Doc: https://ffmpeg.org/ffmpeg-filters.html#palettegen
    palettegen = 'palettegen=max_colors={colors}:reserve_transparent=off'.format(**preset)
    if preset['palette_diff']:
        palettegen += ':stats_mode=diff'

    # Paletteuse ####
    # Doc: https://ffmpeg.org/ffmpeg-filters.html#paletteuse
    paletteuse = 'paletteuse'
    dither = preset['dither']
    if dither:
        if dither.startswith('bayer') and dither != 'bayer':
            paletteuse += '=dither=bayer:bayer_scale={}'.format(dither[5:])
        else:
            paletteuse += '=dither={dither}'.format(**preset)

    log.info("Converting %s to %s..." % (filename, basename(out_path)))
    filtergraph = ';'.join((
        # Perform conversion and split stream into [tmp1], [tmp2]
        ','.join(conversion + ['split']) + '[tmp1][tmp2]',
        # Feed [tmp1] into palettegen and store palette in [pal]
        '[tmp1]' + palettegen + '[pal]',
        # Use palette [pal] and [tmp2] to generate the final gif
        '[tmp2][pal]' + paletteuse
    ))

    call_command([*cmd, '-i', path, '-filter_complex', filtergraph, out_path])

    log.info("Completed %s (%sB)" % (basename(out_path), pretty_size(getsize(out_path))))
    return out_path


def convert(path):
    # noinspection PyBroadException
    try:
        return convert_inner(path)
    except Exception:
        logging.error("Error converting %s", path, exc_info=True)
        return None


def optional(argtype):
    def convert_arg(value):
        if value in ('max', 'off'):
            return None
        else:
            return argtype(value)
    return convert_arg


def tuple_arg(argtype, maxargs):
    def convert_arg(value):
        value = value.split(',', maxargs + 1)
        return tuple(map(argtype, value))
    return convert_arg


# Argument parsing. Keep this together with main()
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-s', '--start', default=0,
                    help='start time, offset in seconds')
parser.add_argument('-l', '--length', default='10', type=optional(str),
                    help='length of output in seconds. Pass "max" to disable.')
parser.add_argument('-f', '--fps', default=20, type=optional(float),
                    help='frames per second. Pass "max" to disable')
parser.add_argument('-d', '--scale', default=500, type=optional(int),
                    help='maximum dimensions of output. Pass "max" to disable. '
                         'Aspect ratio is always kept and will never be upscaled.')
parser.add_argument('-c', '--colors', default=128, type=int,
                    help='maximum colors in palette')
parser.add_argument('--no-palette-diff', default=True, dest='palette_diff', action='store_false',
                    help='generate palette based on differences only')
parser.add_argument('--dither', default='sierra2_4a',
                    choices=('none', 'floyd_steinberg', 'sierra2', 'sierra2_4a',
                             'bayer', 'bayer1', 'bayer2', 'bayer3', 'bayer4', 'bayer5'),
                    help='dithering algorithm')
parser.add_argument('--ppdenoise', default=False, action='store_true',
                    help='reduce noise using lipostproc tmpnoise filter. Works well with --dither=bayer')
parser.add_argument('--atadenoise', default=False, action='store_true',
                    help='reduce noise using FFmpeg atadenoise filter. Works well with sierra (default) dithering')
parser.add_argument('-p', '--play', default=False, action='store_true',
                    help='play files after conversion')
parser.add_argument('--crop-left',   '--left',   default=0, type=float, help='crop percentage from left side')
parser.add_argument('--crop-right',  '--right',  default=0, type=float, help='crop percentage from right side')
parser.add_argument('--crop-top',    '--top',    default=0, type=float, help='crop percentage from top')
parser.add_argument('--crop-bottom', '--bottom', default=0, type=float, help='crop percentage from bottom')
parser.add_argument('--slower', default=0, type=float, help='make viedeo slower by percent')
parser.add_argument('--faster', default=0, type=float, help='make video faster by percent')
parser.add_argument('files', metavar='FILE', nargs='+',
                    help='input filenames')
parser.add_argument('-q', '--quiet', dest='verbosity', default=0, action='store_const', const=-1,
                    help='silence information messages')
parser.add_argument('-v', '--verbose', dest='verbosity', default=0, action='count',
                    help='more verbose output')


def main():
    global preset

    args = parser.parse_args()
    preset = vars(args)

    if args.verbosity <= -1:
        level = logging.WARNING
    elif args.verbosity == 0:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(level=level, format='%(message)s')

    parallel = len(os.sched_getaffinity(0))
    with ThreadPoolExecutor(parallel) as executor:
        outputs = [f for f in executor.map(convert, args.files) if f is not None]
        executor.shutdown()

    if len(args.files) > 1:
        log.info("Converted %d files (%d skips/failures)" % (len(outputs), len(args.files) - len(outputs)))

    # Create this file to enable command log
    logfile = expanduser('~/.vigif.log')
    if outputs and exists(logfile):
        with open(logfile, 'a') as f:
            f.write(escape_shell_command(sys.argv) + '\n')

    if outputs and args.play:
        log.info("")
        try:
            call_command(['mpv', '--loop-file', '--', *outputs])
        except CalledProcessError as err:
            log.error("Error playing: %s" % err)
            sys.exit(2)

    if not outputs:
        # Unsuccessful
        sys.exit(1)


if __name__ == '__main__':
    main()
