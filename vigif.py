#!/usr/bin/python3
"""
See:
https://superuser.com/a/556031
http://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html

* The giftool that keeps on giffing!
* Keep calm and gif on!
"""
import logging
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from os.path import basename, splitext, isfile, exists, getsize
from subprocess import check_call
from tempfile import NamedTemporaryFile


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


preset = {
    'start': 0.0,
    'length': 10.0,
    'fps': 20,
    'scale': 640,
    'colors': 256,
    'palette_diff': True,
    'dither': 'sierra2_4a',
}


def convert_inner(path):
    filename = basename(path)
    out_path = splitext(filename)[0] + '.gif'

    if not exists(path):
        print("Does not exist: %s" % path)
        return

    if path.endswith('.gif') or not isfile(path):
        print("Skipping: %s" % filename)
        return

    if exists(out_path):
        print("WARN: Overwriting %s" % out_path)

    cmd = 'ffmpeg', '-y', '-loglevel', '31'

    # Cut ####
    if preset['start']:
        cmd += '-ss', str(preset['start'])
    if preset['length']:
        cmd += '-t', str(preset['length'])

    # Conversion ####
    conversion = []

    if preset['fps']:
        conversion.append('fps={fps}'.format(**preset))
    if preset['scale']:
        # Doc: https://trac.ffmpeg.org/wiki/Scaling
        conversion.append("scale='min(iw,{scale})':'min(ih,{scale})':"
                          "force_original_aspect_ratio=decrease:flags=lanczos"
                          .format(**preset))

    conversion = ','.join(conversion)

    # Palettegen ####
    # Doc: https://ffmpeg.org/ffmpeg-filters.html#palettegen
    palettegen = 'palettegen=max_colors={colors}:reserve_transparent=off'.format(**preset)
    if preset['palette_diff']:
        palettegen += ':stats_mode=diff'

    # Paletteuse ####
    # Doc: https://ffmpeg.org/ffmpeg-filters.html#paletteuse
    paletteuse = 'paletteuse'
    if preset['dither']:
        paletteuse += '=dither={dither}'.format(**preset)

    print("Converting %s to %s..." % (filename, basename(out_path)))
    with NamedTemporaryFile(prefix='pal', suffix='.png') as palette:
        check_call([*cmd,
                    '-i', path,
                    '-vf', conversion + ',' + palettegen,
                    palette.name])

        check_call([*cmd,
                    '-i', path, '-i', palette.name,
                    '-filter_complex', conversion + '[x];[x][1:v]' + paletteuse,
                    out_path])

    print("Completed %s (%sB)" % (basename(out_path), pretty_size(getsize(out_path))))
    return True


def convert(path):
    # noinspection PyBroadException
    try:
        return convert_inner(path)
    except Exception:
        logging.error("Error converting %s", path, exc_info=True)


def main():
    files = sys.argv[1:]

    parallel = len(os.sched_getaffinity(0))
    with ThreadPoolExecutor(parallel) as executor:
        results = list(executor.map(convert, files))
        executor.shutdown()

    success = results.count(True)
    if len(files) > 1:
        print("Converted %d files (%d skips/failures)" % (success, len(files) - success))

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
