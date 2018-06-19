#!/usr/bin/python3
"""
See https://superuser.com/a/556031

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

    print("Converting %s to %s..." % (filename, basename(out_path)))
    with NamedTemporaryFile(prefix='pal', suffix='.png') as palette:
        conversion = 'fps=10,scale=640:-1:flags=lanczos'
        palettegen = 'palettegen=max_colors=90:stats_mode=diff'
        paletteuse = 'paletteuse=dither=bayer'
        check_call(['ffmpeg', '-y',
                    '-loglevel', '31',
                    '-i', path,
                    '-vf', conversion + ',' + palettegen,
                    palette.name])

        check_call(['ffmpeg', '-y',
                    '-loglevel', '31',
                    '-i', path, '-i', palette.name,
                    '-filter_complex', conversion + '[x];[x][1:v]' + paletteuse,
                    out_path])

    print("Completed %s (%sB)" % (basename(out_path), pretty_size(getsize(out_path))))
    return True


def convert(path):
    try:
        return convert_inner(path)
    except Exception as err:
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


if __name__=='__main__':
    main()
