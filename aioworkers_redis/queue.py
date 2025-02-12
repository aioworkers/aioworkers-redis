import asyncio
import time

from aioworkers.queue.base import score_queue

from aioworkers_redis.base import BaseQueue


class Queue(BaseQueue):
    async def put(self, value):
        value = self.encode(value)
        return await self.adapter.rpush(self.key, value)

    async def get(self, *, timeout: float = 0):
        deadline: float = 0
        if timeout:
            deadline = time.monotonic() + timeout
        timeout = max(timeout, self._timeout)

        async with self._lock:
            while True:
                if self._blocking:
                    result = await self.adapter.blpop(self.key, timeout=timeout)
                    for _key, v in result.items():
                        return self.decode(v)
                elif result := await self.adapter.lpop(self.key):
                    return self.decode(result)

                if deadline and time.monotonic() > deadline:
                    raise TimeoutError
                elif not self._blocking:
                    await asyncio.sleep(self._timeout)

    async def length(self):
        return await self.adapter.llen(self.key)

    async def list(self):
        return [self.decode(i) for i in await self.adapter.lrange(self.key, 0, -1)]

    async def remove(self, value):
        value = self.encode(value)
        await self.adapter.lrem(self.key, 0, value)

    async def clear(self):
        return await self.adapter.delete(self.key)


class BaseZQueue(Queue):
    script = ""

    async def put(self, value):
        score, val = value
        val = self.encode(val)
        return await self.adapter.zadd(self.key, {val: score})

    async def get(self, *, timeout: float = 0):
        async with self._lock:
            while True:
                lv = await self.adapter.eval(self.script, 1, self.key)
                if lv:
                    break
                await asyncio.sleep(timeout or self.config.timeout)
        value, score = lv
        return float(score), self.decode(value)

    async def length(self):
        return await self.adapter.zcard(self.key)

    async def list(self):
        return [self.decode(i) for i in await self.adapter.zrange(self.key, 0, -1)]

    async def remove(self, value):
        value = self.encode(value)
        await self.adapter.zrem(self.key, value)


@score_queue("time.time")
class ZQueue(BaseZQueue):
    script = """
        local val = redis.call('zrange', KEYS[1], 0, 0, 'WITHSCORES')
        if val[1] then redis.call('zrem', KEYS[1], val[1]) end
        return val
        """


@score_queue("time.time")
class TimestampZQueue(BaseZQueue):
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

    async def get(self, *, timeout: float = 0):
        async with self._lock:
            while True:
                lv = await self.adapter.eval(self.script, 1, self.key, time.time())
                if lv:
                    break
                await asyncio.sleep(timeout or self.config.timeout)
        value, score = lv
        return float(score), self.decode(value)
