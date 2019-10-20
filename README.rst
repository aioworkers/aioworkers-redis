aioworkers-redis
================

Redis plugin for `aioworkers`.

.. image:: https://travis-ci.org/aioworkers/aioworkers-redis.svg?branch=master
  :target: https://travis-ci.org/aioworkers/aioworkers-redis

.. image:: https://codecov.io/gh/aioworkers/aioworkers-redis/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/aioworkers/aioworkers-redis

.. image:: https://img.shields.io/pypi/v/aioworkers-redis.svg
  :target: https://pypi.python.org/pypi/aioworkers-redis

.. image:: https://pyup.io/repos/github/aioworkers/aioworkers-redis/shield.svg
  :target: https://pyup.io/repos/github/aioworkers/aioworkers-redis/
  :alt: Updates

.. image:: https://readthedocs.org/projects/aioworkers-redis/badge/?version=latest
  :target: http://aioworkers-redis.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

.. image:: https://img.shields.io/pypi/pyversions/aioworkers-redis.svg
  :target: https://pypi.python.org/pypi/aioworkers-redis


Usage
-----

Add this to aioworkers config.yaml:

.. code-block:: yaml

    redis:
        cls: aioworkers_redis.base.Connector
        prefix: app
        connection:
            host: 'localhost'
            port: 6379
            maxsize: 20
    queue:
        cls: aioworkers_redis.queue.Queue
        connection: redis
        format: json
        key: queue

You can work with redis queue like this:

.. code-block:: python

    await context.queue.put({'a': 1})
    d = await context.queue.get()
