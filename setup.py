#!/usr/bin/env python3

import pip
from setuptools import setup


if tuple(map(int, pip.__version__.split('.'))) >= (10, 0, 0):
    # noinspection PyProtectedMember
    from pip._internal.download import PipSession
    # noinspection PyProtectedMember
    from pip._internal.req import parse_requirements
else:
    # noinspection PyUnresolvedReferences
    from pip.download import PipSession
    # noinspection PyUnresolvedReferences
    from pip.req import parse_requirements


install_requires_g = parse_requirements('requirements.txt', session=PipSession())
install_requires = [str(ir.req) for ir in install_requires_g]

dev_requires_g = parse_requirements('requirements-dev.txt', session=PipSession())
dev_requires = [str(ir.req) for ir in dev_requires_g]


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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Multimedia :: Video :: Conversion',
    ],

    # Installation settings
    packages=['kogif'],
    entry_points={'console_scripts': [
        'kogif = kogif.kogif:main',
        'keep-on-giffing = kogif.kogif:main',
    ]},
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
    },
    test_suite='tests',
)
