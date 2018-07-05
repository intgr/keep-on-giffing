#!/usr/bin/python3
"""The gif-tool that keeps on giffing!

Keep on Giffing is a wrapper around FFmpeg for converting video clips from any format to optimized `.gif` files.
FFmpeg has excellent support for outputting optimized GIF files (optimal palette generation, dithering, scaling,
cropping, denoising, etc) but those features are very difficult to use. Keep on Giffing to the rescue, it has a simple
command line syntax and many features for optimizing GIF files.

Helpful posts and articles:
* https://superuser.com/a/556031
* http://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html
* https://superuser.com/a/1275521/18382
* https://stackoverflow.com/a/34338901/177663
"""
import logging
import math
import os
import shlex
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from concurrent.futures import ThreadPoolExecutor
from os.path import basename, splitext, isfile, exists, getsize, expanduser
from subprocess import CalledProcessError, check_call, Popen, PIPE
from typing import List

log = logging.getLogger('kogif')


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


def cpu_count():
    """Returns the number of available CPUs on the machine."""

    if hasattr(os, 'sched_getaffinity'):
        # On Linux, sched_getaffinity returns *usable* CPUs in the current container.
        return len(os.sched_getaffinity(0))
    else:
        return os.cpu_count()


def play_command(filenames: List[str]) -> List[str]:
    return ['mpv', '--loop-file', '--hr-seek=yes', '--'] + filenames


def ffmpeg_command(args: Namespace, path: str, out_path: str) -> List[str]:
    opts = vars(args)

    # FFmpeg loglevel 24 = warning, 16 = error
    cmd = 'ffmpeg', '-y', '-loglevel', ('24' if args.verbosity >= 0 else '16')

    # Cut ####
    if args.start:
        cmd += '-ss', str(args.start)
    if args.length:
        cmd += '-t', str(args.length)

    # Conversion ####
    conversion = []

    if args.slower or args.faster:
        ratio = 1 + (args.slower if 'slower' in opts else -args.faster) / 100
        conversion.append('setpts={}*PTS'.format(ratio))
    if args.fps:
        conversion.append('fps={fps}'.format(**opts))
    if args.crop_left or args.crop_right or args.crop_top or args.crop_bottom:
        conversion.append('crop=in_w*{}:in_h*{}:in_w*{}:in_h*{}'
                          .format(1 - (args.crop_left + args.crop_right) / 100,
                                  1 - (args.crop_top + args.crop_bottom) / 100,
                                  args.crop_left / 100,
                                  args.crop_top / 100))
    if args.scale:
        # Doc: https://trac.ffmpeg.org/wiki/Scaling
        conversion.append('scale=min(iw\\,{scale}):min(ih\\,{scale}):'
                          'force_original_aspect_ratio=decrease:flags=lanczos'
                          .format(**opts))

    if args.ppdenoise:
        # https://ffmpeg.org/ffmpeg-filters.html#pp
        # The defaults are too aggressive, causing annoying artifacts. 1|1|1 seems to work well
        conversion.append('pp=tmpnoise|1|1|1')

    if args.atadenoise:
        # https://ffmpeg.org/ffmpeg-filters.html#toc-atadenoise
        # The defaults are quite good, attempting to "hand-tune" usually makes it worse
        conversion.append('atadenoise')

    # There's also owdenoise but it's extremely slow and not very good

    # Palettegen ####
    # Doc: https://ffmpeg.org/ffmpeg-filters.html#palettegen
    palettegen = 'palettegen=max_colors={colors}:reserve_transparent=off'.format(**opts)
    if args.palette_diff:
        palettegen += ':stats_mode=diff'

    # Paletteuse ####
    # Doc: https://ffmpeg.org/ffmpeg-filters.html#paletteuse
    paletteuse = 'paletteuse'
    if args.dither:
        if args.dither.startswith('bayer') and args.dither != 'bayer':
            paletteuse += '=dither=bayer:bayer_scale={}'.format(args.dither[5:])
        else:
            paletteuse += '=dither={dither}'.format(**opts)

    filtergraph = ';'.join((
        # Perform conversion and split stream into [tmp1], [tmp2]
        ','.join(conversion + ['split']) + '[tmp1][tmp2]',
        # Feed [tmp1] into palettegen and store palette in [pal]
        '[tmp1]' + palettegen + '[pal]',
        # Use palette [pal] and [tmp2] to generate the final gif
        '[tmp2][pal]' + paletteuse
    ))

    return [*cmd, '-i', path, '-filter_complex', filtergraph, '-f', 'gif', out_path]


def run_play_pipeline(cmd: List[str], out_path: str):
    """Perform conversion and playback as a pipeline: start playback before the whole conversion is even finished."""

    tee_cmd = ['tee', '--output-error=warn-nopipe', '--', out_path]
    play_cmd = play_command(['-'])
    log.debug("Running: %s | %s | %s",
              escape_shell_command(cmd), escape_shell_command(tee_cmd), escape_shell_command(play_cmd))

    # XXX PyCharm bug:
    # noinspection PyListCreation
    pipe = []
    pipe.append(Popen(cmd, stdout=PIPE))
    pipe.append(Popen(tee_cmd, stdin=pipe[-1].stdout, stdout=PIPE))
    pipe.append(Popen(play_cmd, stdin=pipe[-1].stdout))

    # Close our copy of file descriptors, otherwise we deadlock
    pipe[0].stdout.close()
    pipe[1].stdout.close()

    # Wait for them all to quit...
    for proc in pipe:
        ret = proc.wait()
        # Report error, except that we don't care about mpv failing
        if ret != 0 and proc != pipe[2]:
            raise CalledProcessError(ret, proc.args)


def convert_inner(args: Namespace, path: str):
    filename = basename(path)
    out_path = splitext(filename)[0] + '.gif'

    if not exists(path):
        log.error("Does not exist: %s" % path)
        return None

    if path.endswith('.gif') or not isfile(path):
        log.warning("Skipping gif: %s" % filename)
        return None

    if exists(out_path):
        log.warning("WARN: Overwriting %s" % out_path)

    log.info("Converting %s to %s..." % (filename, basename(out_path)))

    if args.play == 'pipe':
        cmd = ffmpeg_command(args, path, '-')
        run_play_pipeline(cmd, out_path)
    else:
        cmd = ffmpeg_command(args, path, out_path)
        check_call(cmd)

    log.info("Completed %s (%sB)" % (basename(out_path), pretty_size(getsize(out_path))))
    return out_path


def convert_wrapper(args: Namespace, path: str):
    """Error-handling-reporting wrapper for multithreaded execution."""
    # noinspection PyBroadException
    try:
        return convert_inner(args, path)
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
                         'Aspect ratio is kept and video is never upscaled.')
parser.add_argument('-c', '--colors', default=256, type=int,
                    help='maximum unique colors in palette')
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
                    help='play resulting gif files using mpv')
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


def run_convert(args: Namespace):
    if len(args.files) == 1:
        outputs = [convert_inner(args, args.files[0])]
    else:
        # Use parallelization and wrapper
        with ThreadPoolExecutor(cpu_count()) as executor:
            outputs = executor.map(lambda f: convert_wrapper(args, f), args.files)
            executor.shutdown()

    # Filter out None returns -- failed conversions
    return [f for f in outputs if f]


def main(args=None):
    args = parser.parse_args(args)

    if args.verbosity <= -1:
        level = logging.WARNING
    elif args.verbosity == 0:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logging.basicConfig(level=level, format='%(message)s')

    if args.play:
        # If there's just one output file, we can pipeline playback. Only supported with GNU tee command (on Linux).
        args.play = 'pipe' if len(args.files) == 1 and sys.platform == 'linux' else 'after'

    outputs = run_convert(args)

    if len(args.files) > 1:
        log.info("Converted %d files (%d skips/failures)" % (len(outputs), len(args.files) - len(outputs)))

    # Create this file to enable command log
    logfile = expanduser('~/.keep-on-giffing.log')
    if outputs and exists(logfile):
        with open(logfile, 'a') as f:
            f.write(escape_shell_command(sys.argv) + '\n')

    if outputs and args.play == 'after':
        log.info("")
        try:
            call_command(play_command(outputs))
        except CalledProcessError as err:
            log.error("Error playing: %s" % err)
            sys.exit(2)

    if not outputs:
        # Unsuccessful
        sys.exit(1)


if __name__ == '__main__':
    main()
