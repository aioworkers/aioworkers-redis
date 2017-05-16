from aioworkers.storage.base import AbstractListedStorage, FieldStorageMixin

from aioworkers_redis.base import Connector


class Storage(Connector, AbstractListedStorage):
    async def list(self):
        async with self.pool as conn:
            l = await conn.keys(self.raw_key('*'))
        return [self.clean_key(i) for i in l]

    async def length(self):
        async with self.pool as conn:
            l = await conn.keys(self.raw_key('*'))
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


class HashStorage(FieldStorageMixin, Storage):

    async def set(self, key, value, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        to_del = []
        async with self.pool as conn:
            if field:
                if value is None:
                    to_del.append(field)
                else:
                    return await conn.hset(raw_key, field, self.encode(value))
            elif value is None:
                return await conn.delete(raw_key)
            else:
                pairs = []
                for f in fields or value:
                    v = value[f]
                    if v is None:
                        to_del.append(f)
                    else:
                        pairs.extend((f, self.encode(v)))
                if pairs:
                    await conn.hmset(raw_key, *pairs)
            if to_del:
                await conn.hdel(raw_key, *to_del)

    async def get(self, key, *, field=None, fields=None):
        raw_key = self.raw_key(key)
        async with self.pool as conn:
            if field:
                return self.decode(await conn.hget(raw_key, field))
            elif fields:
                v = await conn.hmget(raw_key, *fields)
                m = self.model()
                for f, v in zip(fields, v):
                    m[f] = self.decode(v)
            else:
                a = await conn.hgetall(raw_key)
                m = self.model()
                for f, v in a.items():
                    m[f.decode()] = self.decode(v)
            return m
