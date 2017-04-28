from aioworkers.storage.base import AbstractListedStorage

from aioworkers_redis.base import RedisPool


class RedisStorage(RedisPool, AbstractListedStorage):
    def init(self):
        self._prefix = self.config.get('prefix')
        return super().init()

    def raw_key(self, key):
        return self._prefix + key

    async def list(self):
        async with self.pool as conn:
            l = await conn.keys(self._prefix + '*')
        p = len(self._prefix)
        return [i[p:].decode() for i in l]

    async def length(self):
        async with self.pool as conn:
            l = await conn.keys(self._prefix + '*')
        return len(l)

    async def set(self, key, value):
        raw_key = self.raw_key(key)
        is_null = value is None
        if not is_null:
            value = self.encode(value)
        async with self.pool as conn:
            if is_null:
                return await conn.delete(raw_key)
            else:
                return await conn.set(raw_key, value)

    async def get(self, key):
        raw_key = self.raw_key(key)
        async with self.pool as conn:
            value = await conn.get(raw_key)
        if value is not None:
            return self.decode(value)
