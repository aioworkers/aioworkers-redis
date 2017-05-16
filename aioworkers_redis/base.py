import aioredis
from aioworkers.core.formatter import FormattedEntity


class Connector(FormattedEntity):
    async def init(self):
        await super().init()
        self._pool = None
        if isinstance(self.config.get('connection'), str):
            path = self.config.connection
            self._connector = self.context[path]
        else:
            self._connector = self
            groups = self.config.get('groups')
            self.context.on_start.append(self.start, groups)
            self.context.on_stop.append(self.stop, groups)

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
                break
        if p:
            p.reverse()
            self._prefix = ''.join(p)
        else:
            self._prefix = ''

    def raw_key(self, key):
        if not self._prefix:
            return key
        return self._prefix + key

    def clean_key(self, raw_key):
        result = raw_key[len(self._prefix):]
        if isinstance(result, str):
            return result
        return result.decode()

    async def start(self):
        if self._connector is not self:
            return

        cfg = self.config.get('connection', {}).copy()
        address = cfg.pop('host', 'localhost'), cfg.pop('port', 6379)
        self._pool = await aioredis.create_pool(
            address, **cfg, loop=self.loop)

    async def stop(self):
        if self._connector is not self:
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
