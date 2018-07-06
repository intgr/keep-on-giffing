"""Fixtures for unit tests"""
import logging
import os
from os.path import exists
from pathlib import Path
from urllib.request import urlretrieve

import pytest

CACHE_DIR = Path(__file__).parent.parent / '.pytest_cache'

BBB_FILENAME = 'Big_Buck_Bunny_Trailer_400p.ogv.160p.webm'
#: Tiny Big Buck Bunny trailer, 180p, from Wikimedia Commons (Wikipedia)
BBB_URL = ('https://upload.wikimedia.org/wikipedia/commons/transcoded/b/b3/Big_Buck_Bunny_Trailer_400p.ogv/'
           + BBB_FILENAME)


log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def cache_dir() -> Path:
    """Creates cache directory if necessary and returns its path."""

    if not CACHE_DIR.exists():
        os.mkdir(str(CACHE_DIR))
    return CACHE_DIR


@pytest.fixture(scope='session')
def test_video(cache_dir) -> str:
    """Returns path to test trailer. Downloads the file if it's not already cached."""

    path = cache_dir / BBB_FILENAME
    if not path.exists():
        log.warning("Downloading sample file to %s", path)
        urlretrieve(BBB_URL, str(path))

    return str(path)


@pytest.fixture
def test_output() -> str:
    """Returns path to output file. Deletes the file if it already exists from a previous test or run."""
    # In the current directory
    path = BBB_FILENAME.replace('.webm', '.gif')
    assert not exists(path)
    return str(path)


@pytest.fixture
def chdir_tmp(tmpdir):
    """Change to a temporary directory and change back later."""
    old_dir = os.getcwd()
    try:
        os.chdir(str(tmpdir))
        yield tmpdir
    finally:
        os.chdir(old_dir)
