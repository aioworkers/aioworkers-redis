from aioworkers.storage.base import (
    AbstractBaseStorage,
    AbstractExpiryStorage,
    AbstractListedStorage,
    FieldStorageMixin,
)

from aioworkers_redis.base import Connector, KeyEntity


class Storage(Connector, AbstractListedStorage, AbstractExpiryStorage):
    _expiry = None

    def set_config(self, config):
        super().set_config(config)
        self._expiry = self.config.get_duration(
            'expiry', default=None, null=True,
        )

    async def list(self):
        async with self.acquire() as conn:
            keys = await conn.execute('keys', self.raw_key('*'))
        return [self.clean_key(i) for i in keys]

    async def length(self):
        async with self.acquire() as conn:
            keys = await conn.execute('keys', self.raw_key('*'))
        return len(keys)

    async def set(self, key, value):
        raw_key = self.raw_key(key)
        is_null = value is None
        if not is_null:
            value = self.encode(value)
        async with self.acquire() as conn:
            if is_null:
                return await conn.execute('del', raw_key)
            elif self._expiry:
                return await conn.execute(
                    'setex', raw_key, self._expiry, value,
                )
            else:
                return await conn.execute('set', raw_key, value)

    async def get(self, key):
        raw_key = self.raw_key(key)
        async with self.acquire() as conn:
            value = await conn.execute('get', raw_key)
        if value is not None:
            return self.decode(value)

    async def expiry(self, key, expiry):
        raw_key = self.raw_key(key)
        async with self.acquire() as conn:
            await conn.execute('expire', raw_key, expiry)


class HashStorage(FieldStorageMixin, Storage):

    async def set(self, key, value, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        to_del = []
        async with self.acquire() as conn:
            if field:
                if value is None:
                    to_del.append(field)
                else:
                    return await conn.execute(
                        'hset', raw_key, field, self.encode(value),
                    )
            elif value is None:
                return await conn.execute('del', raw_key)
            else:
                pairs = []
                for f in fields or value:
                    v = value[f]
                    if v is None:
                        to_del.append(f)
                    else:
                        pairs.extend((f, self.encode(v)))
                if pairs:
                    await conn.execute('hmset', raw_key, *pairs)
            if to_del:
                await conn.execute('hdel', raw_key, *to_del)
            if self._expiry:
                await conn.execute('expire', raw_key, self._expiry)

    async def get(self, key, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        async with self.acquire() as conn:
            if field:
                return self.decode(await conn.execute('hget', raw_key, field))
            elif fields:
                v = await conn.execute('hmget', raw_key, *fields)
                m = self.model()
                for f, v in zip(fields, v):
                    m[f] = self.decode(v)
            else:
                a = await conn.execute('hgetall', raw_key)
                m = self.model()
                a = iter(a)
                for f, v in zip(a, a):
                    m[f.decode()] = self.decode(v)
            return m


class HyperLogLogStorage(KeyEntity, AbstractBaseStorage):
    async def set(self, key, value=True):
        assert value is True
        async with self.acquire() as conn:
            await conn.execute('pfadd', self.key, key)

    async def get(self, key):
        tmp_key = self.raw_key('tmp:hhl:' + key)
        async with self.acquire() as conn:
            await conn.execute('pfmerge', tmp_key, self.key)
            result = await conn.execute('pfadd', tmp_key, key)
            await conn.execute('del', tmp_key)
        return result == 0

    async def length(self):
        async with self.acquire() as conn:
            c = await conn.execute('pfcount', self.key)
        return c
