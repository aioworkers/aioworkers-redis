import time
import uuid
from unittest import mock

import pytest
from aioworkers.core.context import Context


@pytest.fixture
def config_yaml():
    return """
    q:
        key: {uuid}
    """.format(uuid=uuid.uuid4())


async def test_queue(config, event_loop):
    config.update(q=dict(cls='aioworkers_redis.queue.Queue'))
    async with Context(config, loop=event_loop) as ctx:
        q = ctx.q
        await q.put(3)
        assert 1 == await q.length()
        assert [b'3'] == await q.list()
        assert b'3' == await q.get()
        await q.put(3)
        assert 1 == await q.length()
        await q.clear()
        assert not await q.length()
        await q.put(3)
        assert 1 == await q.length()
        await q.remove(3)
        assert not await q.length()
        with pytest.raises(TimeoutError):
            await q.get(timeout=1)


async def test_nested_queue(config, event_loop):
    config.update(q=dict(cls='aioworkers_redis.queue.Queue', format='json'))
    async with Context(config, loop=event_loop) as ctx:
        q = ctx.q
        q_child = q.child
        await q_child.put(1)
        assert q_child._key == config.q.key + ':child'
        assert 1 == await q_child.get()


async def test_queue_json(config, event_loop):
    config.update(q=dict(cls='aioworkers_redis.queue.Queue', format='json'))
    async with Context(config, loop=event_loop) as ctx:
        q = ctx.q
        await q.put({'f': 3})
        assert 1 == await q.length()
        assert [{'f': 3}] == await q.list()
        assert {'f': 3} == await q.get()
        await q.put({'f': 3})
        assert 1 == await q.length()
        await q.clear()
        assert not await q.length()


async def test_zqueue(config, event_loop):
    config.update(q=dict(
        cls='aioworkers_redis.queue.ZQueue',
        format='json',
        timeout=0,
    ))
    async with Context(config, loop=event_loop) as ctx:
        q = ctx.q
        await q.put('a', 4)
        await q.put('c', 3)
        await q.put('b', 2)
        await q.put('a', 1)
        assert 3 == await q.length()
        assert ['a', 'b', 'c'] == await q.list()
        assert 3 == await q.length()
        assert 'a' == await q.get()
        assert ['b', 'c'] == await q.list()
        assert 2 == await q.length()
        assert 'b' == await q.get()
        assert ['c'] == await q.list()
        assert 1 == await q.length()
        assert 'c' == await q.get()
        assert [] == await q.list()
        assert not await q.length()
        await q.put('3')
        assert 1 == await q.length()
        await q.remove('3')
        assert not await q.length()
        with mock.patch('asyncio.sleep', object()):
            with pytest.raises(TypeError):
                await q.get()


async def test_ts_zqueue(config, event_loop):
    config.update(q=dict(
        cls='aioworkers_redis.queue.TimestampZQueue',
        format='json',
        timeout=10,
    ))
    async with Context(config, loop=event_loop) as ctx:
        q = ctx.q
        await q.put('c', time.time() + 4)
        await q.put('a', 4)
        assert 2 == await q.length()
        assert ['a', 'c'] == await q.list()
        assert 'a' == await q.get()
        assert 1 == await q.length()
        assert ['c'] == await q.list()

        async def breaker(*args, **kwargs):
            raise InterruptedError

        with mock.patch('asyncio.sleep', breaker):
            with pytest.raises(InterruptedError):
                await q.get()
