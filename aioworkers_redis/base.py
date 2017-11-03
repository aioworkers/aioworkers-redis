import logging

import aioredis
from aioworkers.core.base import AbstractNestedEntity
from aioworkers.core.formatter import FormattedEntity


logger = logging.getLogger('aioworkers_redis')


class Connector(AbstractNestedEntity, FormattedEntity):
    async def init(self):
        await super().init()
        self._fut_pool = self.loop.create_future()
        self._prefix = self.config.get('prefix', '')
        self._joiner = self.config.get('joiner', ':')
        self._connector = self
        groups = self.config.get('groups')
        self.context.on_start.append(self.start, groups)
        self.context.on_stop.append(self.stop, groups)

    def factory(self, item):
        inst = super().factory(item)
        inst._connector = self._connector
        inst._joiner = self._joiner
        inst._formatter = self._formatter
        inst._prefix = self.raw_key(item)
        return inst

    def raw_key(self, key):
        k = self._prefix, key
        k = [i for i in k if i] or ''
        return self._joiner.join(k)

    def clean_key(self, raw_key):
        result = raw_key[len(self._prefix) + len(self._joiner):]
        if isinstance(result, str):
            return result
        return result.decode()

    async def get_pool(self):
        fp = self._connector._fut_pool
        if not fp.done():
            return await fp
        elif fp.cancelled():
            raise RuntimeError('Pool not ready')
        elif fp.exception():
            raise fp.exception()
        else:
            return fp.result()

    async def acquire(self):
        pool = await self.get_pool()
        return pool.get()

    async def start(self):
        if self._fut_pool.done():
            return

        connect_params = None

        if isinstance(self.config.get('connection'), str):
            path = self.config.connection
            self._connector = self.context[path]
        else:
            self._connector = self
            connect_params = self.config.get('connection', {})

        # gen prefix
        p = []
        c = self
        while True:
            pref = c.config.get('prefix')
            if pref:
                p.append(pref)
            if c._connector is not c:
                c = c._connector
            else:
                if self.config.get('connect'):
                    self._connector = self
                    connect_params = c.config.get('connection', {})
                break
        if p:
            p.reverse()
            self._prefix = ''.join(p)

        if connect_params is None:
            return

        cfg = connect_params.copy()
        address = cfg.pop('host', 'localhost'), cfg.pop('port', 6379)
        try:
            pool = await aioredis.create_pool(address, **cfg, loop=self.loop)
        except OSError as e:
            logger.critical('An error occurred while connecting to the redis %s', e)
            return
        self._fut_pool.set_result(pool)

    async def stop(self):
        if self._connector is not self:
            return
        pool = await self.get_pool()
        pool.close()
        await pool.wait_closed()
        self._fut_pool = self.loop.create_future()

    def decode(self, b):
        if b is not None:
            return super().decode(b)

    def encode(self, b):
        if b is not None:
            return super().encode(b)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
