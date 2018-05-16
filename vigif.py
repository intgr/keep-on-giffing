#!/usr/bin/python3
"""
See https://superuser.com/a/556031
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from subprocess import check_call
from tempfile import NamedTemporaryFile


def convert(path):
    filename = os.path.basename(path)
    out_path = os.path.splitext(path)[0] + '.gif'
    if out_path == path:
        print("Skipping %s" % filename)
        return

    print("Generating palette for %s..." % filename)
    with NamedTemporaryFile(prefix='pal', suffix='.png') as palette:
        conversion = 'fps=10,scale=640:-1:flags=lanczos'
        check_call(['ffmpeg', '-y',  # '-ss', '30', '-t', '3',
                    '-loglevel', '31',
                    '-i', path,
                    '-vf', conversion + ',palettegen',
                    palette.name])
        print("Converting %s to %s..." % (filename, os.path.basename(out_path)))
        check_call(['ffmpeg', '-y',  # '-ss', '30', '-t', '3',
                    '-loglevel', '31',
                    '-i', path, '-i', palette.name,
                    '-filter_complex', conversion + '[x];[x][1:v]paletteuse',
                    out_path])
    print("Completed %s..." % os.path.basename(os.path.basename(out_path)))


def main():
    parallel = len(os.sched_getaffinity(0))
    with ThreadPoolExecutor(parallel) as executor:
        # jobs = [executor.submit(convert, path)]
        for path in sys.argv[1:]:
            executor.submit(convert, path)

        executor.shutdown()


if __name__=='__main__':
    main()
