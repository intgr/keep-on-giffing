Keep on Giffing (also kogif)
============================

.. pull-quote:: Is the gif-tool that keeps on giffing!

Keep on Giffing is a wrapper around FFmpeg for converting video clips from any format to optimized ``.gif`` files.
FFmpeg has excellent support for outputting optimized GIF files (optimal palette generation, dithering, scaling,
cropping, denoising, etc) but those features are very difficult to use directly. *Keep on Giffing* to the rescue, it has
a simple command line syntax and many features for working with GIF files.

.. image:: https://travis-ci.org/intgr/keep-on-giffing.svg?branch=master
   :alt: Travis CI
   :target: http://travis-ci.org/intgr/keep-on-giffing

.. contents:: Table of contents
    :backlinks: none

Tutorial
========

.. pull-quote:: Keep calm and gif on!

At its most basic, kogif simply takes video files as command line arguments and outputs those files in ``.gif`` format::

    % keep-on-giffing big_buck_bunny_trailer.webm
    Converting big_buck_bunny_trailer.webm to big_buck_bunny_trailer.gif...
    Completed big_buck_bunny_trailer.gif (5.92MB)

.. image:: https://raw.githubusercontent.com/intgr/static/master/keep-on-giffing/big_buck_bunny_trailer.gif

Since the GIF format has poor compression, kogif applies some *default* restrictions already:

* Clip length is **10 seconds**. (To override use ``--length=max``)
* Frame rate is capped at **20 FPS**. (To override use ``--fps=max``)
* Video scaled down to limit width/height to **500 pixels**. (To override use ``--scale=max``)
* Output can have only 256 unique colors (due to limitations of the GIF file format).
* GIF does not support audio.

It often takes some trial and error to get everything right; use ``--play`` to see the result immediately after
conversion is finished. (Requires the ``mpv`` program)

To cut out certain part of the video, note the time codes in your video player and use ``--start`` and ``--length``
arguments. These accept seconds or HH:MM:SS.nnn format::

    keep-on-giffing big_buck_bunny_trailer.webm --play --start=0:14.2 --length=3.4

.. image:: https://raw.githubusercontent.com/intgr/static/master/keep-on-giffing/big_buck_bunny_clip.gif

Optimization
````````````
To reduce the size of the generated GIF file, there are a few tricks...

Play around with the ``--dither`` option. This determines how the limited color palette will be used in the file.
Rule of thumb: use the default (``sierra2_4a``) for fast-moving videos. Use ``--dither=bayer`` if there is static
content (e.g. static background and non-moving camera angle). If that causes too much "crosshatch" pattern for your
tastes then ``bayer3``...``bayer5`` will reduce that. Occasionally ``--dither=none`` leads to better results too.

Reduce noise using ``--ppdenoise``, or if that causes artifacts, ``--atadenoise``. This removes tiny differences across
frames and improves the compression ratio; the difference is mostly imperceptible to the eye.

If you want to reduce the file further, try changing the values of ``--colors``, ``--fps`` and ``--scale``.

With that we have::

    keep-on-giffing big_buck_bunny_trailer.webm -p -s0:14.2 -l3.4 --dither=bayer4 --ppdenoise

Which reduces the size from 3.99 MB to just 1.42 MB!

.. image:: https://raw.githubusercontent.com/intgr/static/master/keep-on-giffing/big_buck_bunny_optimized.gif

Additional tuning
`````````````````
Keep on Giffing also allows you to crop out a portion of the original video using the ``--crop-left``, ``--crop-right``,
``--crop-top`` and ``--crop-bottom`` arguments. For example, ``--crop-right=50`` only keeps the left half of the video.
Note that the ``--scale`` limit is applied *after* cropping.

The video can be sped up or slowed down with ``--faster`` or ``--slower`` arguments, which also take a percentage value.
All together::

    keep-on-giffing big_buck_bunny_trailer.webm -p -s19.9 -l4 --dither bayer4 --play \
        --crop-top 25 --crop-bottom 25 --slower 40

.. image:: https://raw.githubusercontent.com/intgr/static/master/keep-on-giffing/big_buck_bunny_crop.gif

That's it! For the curious, the generated FFmpeg command is::

    ffmpeg -y -loglevel 24 -ss 19.9 -t 4 -i big_buck_bunny_trailer.webm -filter_complex \
        'setpts=1.4*PTS,fps=20,crop=in_w*1.0:in_h*0.5:in_w*0.0:in_h*0.25,scale=min(iw\,500):min(ih\,500):\
        force_original_aspect_ratio=decrease:flags=lanczos,split[tmp1][tmp2];[tmp1]palettegen=max_colors=256:\
        reserve_transparent=off:stats_mode=diff[pal];[tmp2][pal]paletteuse=dither=bayer:bayer_scale=4' \
        big_buck_bunny_trailer.gif


Installation
============

.. pull-quote:: Gif it a chance!

Tested on Linux and macOS. Most Linux installations will already have the following requirements:

* Python 3.5 or newer
* FFmpeg
* mpv (only if you want to use ``--play``)


Credit is due
=============

* Keep on Giffing is written by Marti Raudsepp
* Thanks to FFmpeg for doing all the actual hard work!
* `Several <https://superuser.com/a/556031>`_ `StackOverflow <https://superuser.com/a/1275521/18382>`_
  `answers <https://stackoverflow.com/a/34338901/177663>`_.
* Inspired somewhat by the `Gifcurry tool <https://github.com/lettier/gifcurry>`_, by David Lettier.
