#!/usr/bin/env python

from setuptools import setup, find_packages

requirements = [
    'aioworkers>=0.8.0',
    'aioredis==1.1.0',
]

test_requirements = [
    'pytest',
]

setup(
    name='aioworkers-redis',
    version='0.4.3',
    description="Module for working with redis",
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
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
