import aioredis
from aioworkers.core.formatter import FormattedEntity


class Connector(FormattedEntity):
    async def init(self):
        await super().init()
        self._pool = None
        if isinstance(self.config.connection, str):
            path = self.config.connection
            self._connector = self.context[path]
        else:
            self._connector = self
            groups = self.config.get('groups')
            self.context.on_start.append(self.start, groups)
            self.context.on_stop.append(self.stop, groups)

    @property
    def prefix(self):
        return self._connector.config.get('prefix', '')

    def raw_key(self, key):
        prefix = self.prefix
        if not prefix:
            return key
        return prefix + key

    async def start(self):
        cfg = self.config.connection
        if isinstance(cfg, str):
            return

        cfg = cfg.copy()
        address = cfg.pop('host', 'localhost'), cfg.pop('port', 6379)
        self._pool = await aioredis.create_pool(
            address, **cfg, loop=self.loop)

    async def stop(self):
        if isinstance(self.config.connection, str):
            return
        self._pool.close()
        await self._pool.wait_closed()
        self._pool = None

    @property
    def pool(self):
        return self._connector._pool.get()

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
