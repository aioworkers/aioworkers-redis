#!/usr/bin/env python
import pathlib

from setuptools import setup, find_packages

version = __import__('aioworkers_redis').__version__

requirements = [
    'aioworkers>=0.8.0',
    'aioredis==1.1.0',
]

test_requirements = [
    'pytest',
]

readme = pathlib.Path('README.rst').read_text()

setup(
    name='aioworkers-redis',
    version=version,
    description="Module for working with redis",
    long_description=readme,
    author="Alexander Malev",
    author_email='yttrium@somedev.ru',
    url='https://github.com/aioworkers/aioworkers-redis',
    packages=[i for i in find_packages() if i.startswith('aioworkers_redis')],
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    keywords='aioworkers redis',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
