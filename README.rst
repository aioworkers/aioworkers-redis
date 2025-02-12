aioworkers-redis
================

Redis plugin for `aioworkers`.

.. image:: https://img.shields.io/pypi/v/aioworkers-redis.svg
  :target: https://pypi.org/project/aioworkers-redis

.. image:: https://github.com/aioworkers/aioworkers-redis/workflows/Tests/badge.svg
  :target: https://github.com/aioworkers/aioworkers-redis/actions?query=workflow%3ATests

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json
  :target: https://github.com/charliermarsh/ruff
  :alt: Code style: ruff

.. image:: https://img.shields.io/badge/types-Mypy-blue.svg
  :target: https://github.com/python/mypy
  :alt: Code style: Mypy

.. image:: https://readthedocs.org/projects/aioworkers-redis/badge/?version=latest
  :target: https://github.com/aioworkers/aioworkers-redis#readme
  :alt: Documentation Status

.. image:: https://img.shields.io/pypi/pyversions/aioworkers-redis.svg
  :target: https://pypi.org/project/aioworkers-redis
  :alt: Python versions

.. image:: https://img.shields.io/pypi/dm/aioworkers-redis.svg
  :target: https://pypistats.org/packages/aioworkers-redis

.. image:: https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg
  :alt: Hatch project
  :target: https://github.com/pypa/hatch


Features
--------

* Works on `redis-py <https://pypi.org/project/redis/>`_

* Queue based on
  `RPUSH <https://redis.io/commands/rpush>`_,
  `BLPOP <https://redis.io/commands/blpop>`_,
  `LPOP <https://redis.io/commands/lpop>`_,
  `LLEN <https://redis.io/commands/llen>`_,
  `LRANGE <https://redis.io/commands/lrange>`_

* ZQueue based on
  `ZADD <https://redis.io/commands/zadd>`_,
  `ZRANGE <https://redis.io/commands/zrange>`_,
  `ZCARD <https://redis.io/commands/zcard>`_,
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

* XQueue based on
  `XADD <https://redis.io/commands/xadd>`_,
  `XREADGROUP <https://redis.io/commands/xreadgroup>`_


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


Development
-----------

Check code:

.. code-block:: shell

    hatch run lint:all


Format code:

.. code-block:: shell

    hatch run lint:fmt


Run tests:

.. code-block:: shell

    hatch run pytest


Run tests with coverage:

.. code-block:: shell

    hatch run cov
