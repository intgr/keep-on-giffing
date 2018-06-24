Keep on Giffing (also kogif)
============================

Is the gif-tool that keeps on giffing!

Keep on Giffing is a wrapper around FFmpeg for converting video clips from any format to optimized ``.gif`` files.
FFmpeg has excellent support for outputting optimized GIF files (optimal palette generation, dithering, scaling,
cropping, denoising, etc) but those features are very difficult to use directly. *Keep on Giffing* to the rescue, it has
a simple command line syntax and many features for working with GIF files.


Tutorial
========

Keep calm and gif on!

At its most basic, kogif simply takes video files as command line arguments and outputs those files in ``.gif`` format::

    % keep-on-giffing big_buck_bunny_trailer_480p_logo.webm
    Converting big_buck_bunny_trailer_480p_logo.webm to big_buck_bunny_trailer_480p_logo.gif...
    Completed big_buck_bunny_trailer_480p_logo.gif (5.92MB)

Since the GIF format has poor compression, kogif applies some *default* restrictions already:

* Clip length is 10 seconds. (To override use ``--length=max``)
* Frame rate is capped at 20 FPS. (To override use ``--fps=max``)
* Video scaled down to limit width/height to 500 pixels. (To override use ``--scale=max``)
* Output can have only 256 unique colors (due to limitations of the GIF file format).
* GIF does not support audio.

It Often takes some trial and error to get everything right; use the ``--play`` to see the result immediately when
conversion is finished. (Requires the ``mpv`` program)

To cut out certain part of the video, note the time codes in your video player and use ``--start`` and ``--length``
arguments. These accept seconds or HH:MM:SS.nnn syntax::

    keep-on-giffing big_buck_bunny_trailer_480p_logo.webm --play --start=0:14.2 --length=3.4

Optimization
````````````
To reduce the size of the generated GIF file, there are a few tricks...

Play around with the ``--dither`` option. This determines how the restricted 256-color palette will be used in the file.
Rule of thumb: use defaults for fast-moving videos. Use ``--dither=bayer`` for more static content (e.g. static background
and non-moving camera angle). Occasionally ``--dither=none`` leads to better results too.

Reduce noise using ``--ppdenoise``, or if that causes artifacts, ``--atadenoise``. This removes tiny differences across
frames and improves the compression ratio; the difference is mostly imperceptible to the eye.

If you want to reduce the file further, try changing the values of ``--colors``, ``--fps`` and ``--scale``.

With that we have::

    keep-on-giffing big_buck_bunny_trailer_480p_logo.webm -p -s0:14.2 -l3.4 --dither bayer4 --ppdenoise

Additional tuning
`````````````````
Keep on Giffing also allows you to crop out a portion of the original video using the ``--crop-left``, ``--crop-right``,
``--crop-top`` and ``--crop-bottom`` arguments. For example, ``--crop-right=50`` only keeps the left half of the video.
Note that the ``--scale`` limit is applied *after* cropping.

The video can be sped up or slowed down with ``--faster`` or ``--slower`` arguments, which also take a percentage value.
All together::

    keep-on-giffing big_buck_bunny_trailer_480p_logo.webm -p -s19.9 -l4 --dither bayer4 --play \
        --crop-top 25 --crop-bottom 25 --slower 40

That's it!


Requirements
============

Most Linux installations will already have the following:

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
