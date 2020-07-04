aioworkers-redis
================

Redis plugin for `aioworkers`.

.. image:: https://github.com/aioworkers/aioworkers-redis/workflows/Tests/badge.svg
  :target: https://github.com/aioworkers/aioworkers-redis/actions?query=workflow%3ATests

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


Features
--------

* Works on aioredis
* Queue based on RPUSH, BLPOP, LLEN, LRANGE
* ZQueue based on ZADD, ZRANGE, ZCARD, ZRANGE, ZREM, EVAL
* TimestampZQueue based ZQueue
* Storage based on SET, GET
* HashStorage based on HSET, HGET, HDEL, HMSET, HMGET, HGETALL
* HyperLogLogStorage based on PFADD, PFMERGE, PFCOUNT



Usage
-----

Add this to aioworkers config.yaml:

.. code-block:: yaml

    redis:
        cls: aioworkers_redis.base.Connector
        prefix: app
        connection:
            host: localhost
            port: 6379
            maxsize: 20
    queue:
        cls: aioworkers_redis.queue.Queue
        connection: .redis
        format: json
        key: queue

You can work with redis queue like this:

.. code-block:: python

    await context.queue.put({'a': 1})
    d = await context.queue.get()
