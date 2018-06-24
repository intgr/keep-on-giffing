#!/usr/bin/env python3

from setuptools import setup

setup(
    name='keep-on-giffing',
    version='0.1.0',

    # PyPI metadata
    author='Marti Raudsepp',
    author_email='marti@juffo.org',
    url='https://github.com/intgr/topy',
    download_url='https://pypi.org/project/keep-on-giffing/',
    license='MIT',
    description='Convert videos to GIF format using FFmpeg.',
    long_description=open('README.rst').read(),
    platforms='any',
    keywords='gif convert video ffmpeg',
    classifiers=[
        # https://pypi.org/pypi?:action=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        # Until we have a test suite we're conservative about Python version compatibility claims
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Multimedia :: Video :: Conversion',
    ],

    # Installation settings
    packages=['kogif'],
    entry_points={'console_scripts': [
        'kogif = kogif.kogif:main',
        'keep-on-giffing = kogif.kogif:main',
    ]},
    # test_suite='tests',  # TODO!
)
