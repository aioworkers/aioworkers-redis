import asyncio
import time

from aioworkers.queue.base import AbstractQueue, score_queue

from aioworkers_redis.base import Connector


class Queue(Connector, AbstractQueue):
    async def init(self):
        await super().init()
        self._lock = asyncio.Lock(loop=self.loop)

    @property
    def key(self):
        if not hasattr(self, '_key'):
            self._key = self.raw_key(self.config.key)
        return self._key

    def factory(self, item):
        inst = super().factory(item)
        inst._prefix = self.raw_key(self.config.key)
        inst._key = inst.raw_key(item)
        inst._lock = asyncio.Lock(loop=self.loop)
        return inst

    async def put(self, value):
        value = self.encode(value)
        async with self.acquire() as conn:
            return await conn.execute('rpush', self.key, value)

    async def get(self, *, timeout=0):
        async with self._lock:
            async with self.acquire() as conn:
                result = await conn.execute('blpop', self.key, timeout)
        if timeout and result is None:
            raise TimeoutError
        value = self.decode(result[-1])
        return value

    async def length(self):
        async with self.acquire() as conn:
            return await conn.execute('llen', self.key)

    async def list(self):
        async with self.acquire() as conn:
            return [
                self.decode(i)
                for i in await conn.execute('lrange', self.key, 0, -1)]

    async def remove(self, value):
        value = self.encode(value)
        async with self.acquire() as conn:
            await conn.execute('lrem', self.key, 0, value)

    async def clear(self):
        async with self.acquire() as conn:
            return await conn.execute('del', self.key)


@score_queue('time.time')
class ZQueue(Queue):
    script = """
        local val = redis.call('zrange', KEYS[1], 0, 0, 'WITHSCORES')
        if val[1] then redis.call('zrem', KEYS[1], val[1]) end
        return val
        """

    async def put(self, value):
        score, val = value
        val = self.encode(val)
        async with self.acquire() as conn:
            return await conn.execute('zadd', self.key, score, val)

    async def get(self):
        async with self._lock:
            while True:
                async with self.acquire() as conn:
                    lv = await conn.execute('eval', self.script, 1, self.key)
                if lv:
                    break
                await asyncio.sleep(self.config.timeout, loop=self.loop)
        value, score = lv
        return float(score), self.decode(value)

    async def length(self):
        async with self.acquire() as conn:
            return await conn.execute('zcard', self.key)

    async def list(self):
        async with self.acquire() as conn:
            return [self.decode(i)
                    for i in await conn.execute('zrange', self.key, 0, -1)]

    async def remove(self, value):
        value = self.encode(value)
        async with self.acquire() as conn:
            await conn.execute('zrem', self.key, value)


@score_queue('time.time')
class TimestampZQueue(ZQueue.super):
    script = """
        local val = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
        if val[1] then
            if tonumber(val[2]) < tonumber(ARGV[1]) then
                redis.call('zrem', KEYS[1], val[1])
            else
                return nil
            end
        end
        return val
        """

    async def get(self):
        async with self._lock:
            while True:
                async with self.acquire() as conn:
                    lv = await conn.execute(
                        'eval', self.script, 1, self.key, time.time())
                if lv:
                    break
                await asyncio.sleep(self.config.timeout, loop=self.loop)
        value, score = lv
        return float(score), self.decode(value)
