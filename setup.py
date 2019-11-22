#!/usr/bin/env python
import re
from pathlib import Path

from setuptools import find_packages, setup

PACKAGE = 'aioworkers_redis'
PACKAGE_DIR = Path(__file__).parent / PACKAGE


def read(f):
    path = Path(__file__).parent / f
    if not path.exists():
        return ''
    return path.read_text(encoding='latin1').strip()


def get_version():
    text = read(PACKAGE_DIR / 'version.py')
    if not text:
        text = read(PACKAGE_DIR / '__init__.py')
    try:
        return re.findall(r"\s*__version__ = '([^']+)'$", text, re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


requirements = [
    'aioworkers>=0.14.3',
    'aioredis>=1.3.0',
]

setup(
    name='aioworkers-redis',
    version=get_version(),
    description="Module for working with redis",
    long_description=Path('README.rst').read_text(),
    author="Alexander Malev",
    author_email='yttrium@somedev.ru',
    url='https://github.com/aioworkers/aioworkers-redis',
    packages=find_packages(include=[PACKAGE]),
    include_package_data=True,
    install_requires=requirements,
    python_requires='>=3.6',
    license="Apache Software License 2.0",
    keywords='aioworkers redis',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
