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
        keys = await self.adapter.keys(self.raw_key("*"))
        return [self.clean_key(i) for i in keys]

    async def length(self):
        keys = await self.adapter.keys(self.raw_key("*"))
        return len(keys)

    async def set(self, key, value):
        raw_key = self.raw_key(key)
        is_null = value is None
        if not is_null:
            value = self.encode(value)
        if is_null:
            return await self.adapter.delete(raw_key)
        elif self._expiry:
            return await self.adapter.set(raw_key, value, ex=self._expiry)
        else:
            return await self.adapter.set(raw_key, value)

    async def get(self, key):
        raw_key = self.raw_key(key)
        value = await self.adapter.get(raw_key)
        if value is not None:
            return self.decode(value)

    async def expiry(self, key, expiry):
        raw_key = self.raw_key(key)
        await self.adapter.expire(raw_key, expiry)


class HashStorage(FieldStorageMixin, Storage):
    async def set(self, key, value, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        to_del = []
        if field:
            if value is None:
                to_del.append(field)
            else:
                return await self.adapter.hset(raw_key, field, self.encode(value))
        elif value is None:
            return await self.adapter.delete(raw_key)
        else:
            pairs = {}
            for f in fields or value:
                v = value[f]
                if v is None:
                    to_del.append(f)
                else:
                    pairs[f] = self.encode(v)
            if pairs:
                await self.adapter.hset(raw_key, mapping=pairs)
        if to_del:
            await self.adapter.hdel(raw_key, *to_del)
        if self._expiry:
            await self.adapter.expire(raw_key, self._expiry)

    async def get(self, key, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        if field:
            return self.decode(await self.adapter.hget(raw_key, field))
        elif fields:
            v = await self.adapter.hmget(raw_key, *fields)
            m = self.model()
            for f, val in zip(fields, v):
                m[f] = self.decode(val)
        else:
            a = await self.adapter.hgetall(raw_key)
            m = self.model()
            for f, v in a.items():
                m[f.decode()] = self.decode(v)
        return m


class HyperLogLogStorage(KeyEntity, AbstractBaseStorage):
    async def set(self, key, value=True):
        assert value is True
        await self.adapter.pfadd(self.key, key)

    async def get(self, key):
        tmp_key = self.raw_key("tmp:hhl:" + key)
        await self.adapter.pfmerge(tmp_key, self.key)
        result = await self.adapter.pfadd(tmp_key, key)
        await self.adapter.delete(tmp_key)
        return result == 0

    async def length(self):
        c = await self.adapter.pfcount(self.key)
        return c
