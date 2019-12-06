from typing import Optional, Union

import aioredis
from aioworkers.core.base import (
    AbstractConnector, AbstractNestedEntity, LoggingEntity
)
from aioworkers.core.formatter import FormattedEntity


class Connector(
    AbstractNestedEntity,
    AbstractConnector,
    FormattedEntity,
    LoggingEntity,
):
    skip_child = frozenset(['connection'])

    def __init__(self, *args, **kwargs):
        self._joiner: str = ':'
        self._prefix: str = ''
        self._connector: Optional[Connector] = None
        self._pool: Optional[aioredis.Redis] = None
        super().__init__(*args, **kwargs)

    def set_config(self, config):
        self._joiner = config.get('joiner', ':')
        self._prefix = config.get('prefix', '')
        cfg = config.new_parent(logger='aioworkers_redis')
        super().set_config(cfg)

    @property
    def pool(self) -> aioredis.Redis:
        connector = self._connector or self._get_connector()
        assert connector._pool is not None, 'Pool not ready'
        return connector._pool

    def _get_connector(self) -> 'Connector':
        cfg = self.config.get('connection')
        if isinstance(cfg, str):
            self.logger.debug('Connect to %s', cfg)
            self._connector = self.context.get_object(cfg)
            assert self._connector is not None, 'Not found reference %s' % cfg
        else:
            self._connector = self
        return self._connector

    async def init(self):
        await super().init()
        for k, child in self._children.items():
            if isinstance(child, Connector):
                child._connector = self._connector

    def factory(self, item, config=None):
        if item in self.skip_child:
            return None
        if item not in self._children:
            inst = super().factory(item, config)
            if isinstance(inst, Connector):
                inst._connector = self._connector
                inst._joiner = self._joiner
                inst._formatter = self._formatter
                inst._prefix = self.raw_key(item)
        else:
            inst = self._children[item]
        return inst

    def raw_key(self, key: str) -> str:
        k = [i for i in (self._prefix, key) if i]
        return self._joiner.join(k)

    def clean_key(self, raw_key: Union[str, bytes]) -> str:
        result = raw_key[len(self._prefix) + len(self._joiner):]
        if isinstance(result, str):
            return result
        return result.decode()

    def acquire(self):
        return AsyncConnectionContextManager(self._connector)

    async def connect(self):
        connector = self._connector or self._get_connector()
        if connector is not self:
            return

        cfg = self.config.get('connection')

        c = self
        while True:
            if c._connector is not c:
                c = c._connector
            else:
                if self.config.get('connect'):
                    self._connector = self
                    cfg = c.config.get('connection')
                break
        if cfg:
            cfg = dict(cfg)
        else:
            cfg = {}
        self._pool = await self.pool_factory(cfg)

    async def pool_factory(self, cfg: dict) -> Optional[aioredis.Redis]:
        address = cfg.pop('host', 'localhost'), cfg.pop('port', 6379)
        self.logger.debug('Create pool with address %s', address)
        return await aioredis.create_redis_pool(
            address, **cfg, loop=self.loop,
        )

    async def disconnect(self):
        pool = self._pool
        if pool is not None:
            self.logger.debug('Close pool')
            pool.close()
            await pool.wait_closed()

    def decode(self, b):
        if b is not None:
            return super().decode(b)

    def encode(self, b):
        if b is not None:
            return super().encode(b)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


class AsyncConnectionContextManager:
    __slots__ = ('_connector',)

    def __init__(self, connector: Connector):
        self._connector: Connector = connector

    async def __aenter__(self):
        return self._connector.pool

    async def __aexit__(self, exc_type, exc_value, tb):
        pass
