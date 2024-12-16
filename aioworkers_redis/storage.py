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
            "expiry",
            default=None,
            null=True,
        )

    async def list(self):
        keys = await self.pool.keys(self.raw_key("*"))
        return [self.clean_key(i) for i in keys]

    async def length(self):
        keys = await self.pool.keys(self.raw_key("*"))
        return len(keys)

    async def set(self, key, value):
        raw_key = self.raw_key(key)
        is_null = value is None
        if not is_null:
            value = self.encode(value)
        if is_null:
            return await self.pool.delete(raw_key)
        elif self._expiry:
            return await self.pool.setex(raw_key, self._expiry, value)
        else:
            return await self.pool.set(raw_key, value)

    async def get(self, key):
        raw_key = self.raw_key(key)
        value = await self.pool.get(raw_key)
        if value is not None:
            return self.decode(value)

    async def expiry(self, key, expiry):
        raw_key = self.raw_key(key)
        await self.pool.expire(raw_key, expiry)


class HashStorage(FieldStorageMixin, Storage):
    async def set(self, key, value, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        to_del = []
        if field:
            if value is None:
                to_del.append(field)
            else:
                return await self.pool.hset(raw_key, field, self.encode(value))
        elif value is None:
            return await self.pool.delete(raw_key)
        else:
            pairs = {}
            for f in fields or value:
                v = value[f]
                if v is None:
                    to_del.append(f)
                else:
                    pairs[f] = self.encode(v)
            if pairs:
                await self.pool.hset(raw_key, mapping=pairs)
        if to_del:
            await self.pool.hdel(raw_key, *to_del)
        if self._expiry:
            await self.pool.expire(raw_key, self._expiry)

    async def get(self, key, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        if field:
            return self.decode(await self.pool.hget(raw_key, field))
        elif fields:
            v = await self.pool.hmget(raw_key, *fields)
            m = self.model()
            for f, val in zip(fields, v):
                m[f] = self.decode(val)
        else:
            a = await self.pool.hgetall(raw_key)
            m = self.model()
            for f, v in a.items():
                m[f.decode()] = self.decode(v)
        return m


class HyperLogLogStorage(KeyEntity, AbstractBaseStorage):
    async def set(self, key, value=True):
        assert value is True
        await self.pool.pfadd(self.key, key)

    async def get(self, key):
        tmp_key = self.raw_key("tmp:hhl:" + key)
        await self.pool.pfmerge(tmp_key, self.key)
        result = await self.pool.pfadd(tmp_key, key)
        await self.pool.delete(tmp_key)
        return result == 0

    async def length(self):
        c = await self.pool.pfcount(self.key)
        return c
