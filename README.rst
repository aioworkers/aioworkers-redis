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

* Works on `aioredis <https://pypi.org/project/aioredis/>`_

* Queue based on
  `RPUSH <https://redis.io/commands/rpush>`_,
  `BLPOP <https://redis.io/commands/blpop>`_,
  `LLEN <https://redis.io/commands/llen>`_,
  `LRANGE <https://redis.io/commands/lrange>`_

* ZQueue based on
  `ZADD <https://redis.io/commands/zadd>`_,
  `ZRANGE <https://redis.io/commands/zrange>`_,
  `ZCARD <https://redis.io/commands/zcard>`_,
  `ZRANGE <https://redis.io/commands/zrange>`_,
  `ZREM <https://redis.io/commands/zrem>`_,
  `EVAL <https://redis.io/commands/eval>`_

* TimestampZQueue based ZQueue

* Storage based on
  `SET <https://redis.io/commands/set>`_,
  `GET <https://redis.io/commands/get>`_

* HashStorage based on
  `HSET <https://redis.io/commands/hset>`_,
  `HGET <https://redis.io/commands/hget>`_,
  `HDEL <https://redis.io/commands/hdel>`_,
  `HMSET <https://redis.io/commands/hmset>`_,
  `HMGET <https://redis.io/commands/hmget>`_,
  `HGETALL <https://redis.io/commands/hgetall>`_

* HyperLogLogStorage based on
  `PFADD <https://redis.io/commands/pfadd>`_,
  `PFMERGE <https://redis.io/commands/pfmerge>`_,
  `PFCOUNT <https://redis.io/commands/pfcount>`_


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
