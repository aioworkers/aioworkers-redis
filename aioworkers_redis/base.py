import asyncio
import logging

import aioredis
from aioworkers.core.base import AbstractNestedEntity
from aioworkers.core.formatter import FormattedEntity


logger = logging.getLogger('aioworkers_redis')


class Connector(AbstractNestedEntity, FormattedEntity):
    async def init(self):
        self._connector = None
        self._prefix = None

        if isinstance(self.config.get('connection'), str):
            path = self.config.connection
            self._connector = self.context[path]
        else:
            self._connector = self

        self._ready_pool = asyncio.Event(loop=self.loop)
        await super().init()
        self._joiner = self.config.get('joiner', ':')
        self._pool = None
        self._connect_lock = asyncio.Lock(loop=self.loop)
        groups = self.config.get('groups')
        self.context.on_start.append(self.start, groups)
        self.context.on_stop.append(self.stop, groups)

    def factory(self, item):
        inst = super().factory(item)
        inst._connector = self._connector
        inst._ready_pool = self._ready_pool
        inst._joiner = self._joiner
        inst._formatter = self._formatter
        inst._prefix = self.raw_key(item)
        return inst

    def raw_key(self, key):
        if self._prefix is not None:
            pass
        elif isinstance(self.config.get('connection'), str):
            path = self.config.get('connection')
            self._prefix = self.context[path].raw_key(
                self.config.get('prefix', ''))
        else:
            self._prefix = self.config.get('prefix', '')
        k = self._prefix, key
        k = [i for i in k if i] or ''
        return self._joiner.join(k)

    def clean_key(self, raw_key):
        result = raw_key[len(self._prefix) + len(self._joiner):]
        if isinstance(result, str):
            return result
        return result.decode()

    def acquire(self):
        return AsyncConnectionContextManager(self._connector)

    async def start(self):
        if self._ready_pool.is_set():
            return

        connect_params = None

        if isinstance(self.config.get('connection'), str):
            path = self.config.connection
            self._connector = self.context[path]
        else:
            self._connector = self
            connect_params = self.config.get('connection', {})

        c = self
        while True:
            if c._connector is not c:
                c = c._connector
            else:
                if self.config.get('connect'):
                    self._connector = self
                    connect_params = c.config.get('connection', {})
                break

        if connect_params is None:
            return

        self._connect_params = connect_params
        await self.connect(force=True)

    async def connect(self, force=False):
        if self._connector is not self:
            return
        async with self._connect_lock:
            if force:
                self._ready_pool.clear()
            elif self._ready_pool.is_set():
                return
            cfg = dict(self._connect_params)
            address = cfg.pop('host', 'localhost'), cfg.pop('port', 6379)
            try:
                self._pool = await aioredis.create_pool(address, **cfg, loop=self.loop)
            except OSError as e:
                logger.critical('An error occurred while connecting to the redis %s', e)
                return
            self._ready_pool.set()

    async def stop(self):
        if self._connector is not self:
            return
        elif not self._ready_pool.is_set():
            return
        self._pool.close()
        await self._pool.wait_closed()
        self._ready_pool.clear()

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


class AsyncConnectionContextManager:

    __slots__ = ('_connector', '_conn')

    def __init__(self, connector: Connector):
        self._connector = connector
        self._conn = None

    async def __aenter__(self):
        c = self._connector
        while True:
            await c._ready_pool.wait()
            try:
                self._conn = await c._pool.acquire()
            except aioredis.PoolClosedError:
                c._ready_pool.clear()
                await c.connect()
            else:
                return self._conn

    async def __aexit__(self, exc_type, exc_value, tb):
        try:
            self._connector._pool.release(self._conn)
        finally:
            self._conn = None
