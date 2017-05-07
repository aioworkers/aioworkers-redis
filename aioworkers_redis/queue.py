import asyncio
import time

import aioredis
from aioworkers.queue.base import AbstractQueue, score_queue

from aioworkers_redis.base import Connector


class Queue(Connector, AbstractQueue):
    async def init(self):
        await super().init()
        self._lock = asyncio.Lock(loop=self.loop)
        self._key = self.raw_key(self.config.key)

    async def put(self, value):
        value = self.encode(value)
        async with self.pool as conn:
            return await conn.rpush(self._key, value)

    async def get(self):
        await self._lock.acquire()
        try:
            async with self.pool as conn:
                result = await conn.blpop(self._key)
            self._lock.release()
        except aioredis.errors.PoolClosedError:
            await self._lock.acquire()
        value = self.decode(result[-1])
        return value

    async def length(self):
        async with self.pool as conn:
            return await conn.llen(self._key)

    async def list(self):
        async with self.pool as conn:
            return [
                self.decode(i)
                for i in await conn.lrange(self._key, 0, -1)]

    async def clear(self):
        async with self.pool as conn:
            return await conn.delete(self._key)


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
        async with self.pool as conn:
            return await conn.zadd(self._key, score, val)

    async def get(self):
        await self._lock.acquire()
        while True:
            try:
                async with self.pool as conn:
                    lv = await conn.eval(self.script, [self._key])
            except aioredis.errors.PoolClosedError:
                await self._lock.acquire()
            if lv:
                value, score = lv
                self._lock.release()
                return float(score), self.decode(value)
            await asyncio.sleep(self.config.timeout, loop=self.loop)

    async def length(self):
        async with self.pool as conn:
            return await conn.zcard(self._key)

    async def list(self):
        async with self.pool as conn:
            return [self.decode(i)
                    for i in await conn.zrange(self._key)]


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
        await self._lock.acquire()
        while True:
            try:
                async with self.pool as conn:
                    lv = await conn.eval(
                        self.script, [self._key], [time.time()])
            except aioredis.errors.PoolClosedError:
                await self._lock.acquire()
            if lv:
                value, score = lv
                self._lock.release()
                return float(score), self.decode(value)
            await asyncio.sleep(self.config.timeout, loop=self.loop)
