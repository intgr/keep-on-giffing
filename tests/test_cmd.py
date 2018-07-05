"""Functional tests using the command line interface"""
from os.path import exists

from kogif.kogif import main
# noinspection PyUnresolvedReferences
from .fixtures import cache_dir, test_video, test_output, chdir_tmp


def test_default(test_video, chdir_tmp, test_output):
    """Default execution with no extra arguments"""
    # This is quite slow as it converts the whole 10 seconds :(
    assert not exists(test_output)
    main([test_video])
    assert exists(test_output)


def test_xmastree(test_video, chdir_tmp, test_output):
    """Enable every possible command line option"""

    main(['--start=0:0:26.5',
          '--length=0.2',
          '--fps=25',
          '--scale=150',
          '--colors=128',
          '--no-palette-diff',
          '--dither=bayer3',
          '--ppdenoise',
          '--atadenoise',
          '--crop-left=1.5',
          '--crop-right=15',
          '--crop-top=5',
          '--crop-bottom=0',
          '--slower=40',
          '--verbose',
          test_video])
    assert exists(test_output)
