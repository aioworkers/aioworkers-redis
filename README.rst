aioworkers-redis
================

Redis plugin for `aioworkers`.


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
