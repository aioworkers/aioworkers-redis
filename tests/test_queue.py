import time
import uuid

import pytest
from aioworkers.core.config import MergeDict
from aioworkers.core.context import Context
from aioworkers_redis.queue import Queue, ZQueue, TimestampZQueue


async def test_queue(loop):
    config = MergeDict(key=str(uuid.uuid4()))
    context = Context({}, loop=loop)
    q = Queue(config, context=context, loop=loop)
    await q.init()
    async with q:
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


async def test_nested_queue(loop):
    config = MergeDict(key=str(uuid.uuid4()), format='json', name='q')
    context = Context({}, loop=loop)
    q = Queue(config, context=context, loop=loop)
    await q.init()
    async with q:
        q_child = q.child
        await q_child.put(1)
        assert q_child._key == config.key + ':child'
        assert 1 == await q_child.get()


async def test_queue_json(loop):
    config = MergeDict(
        key=str(uuid.uuid4()),
        format='json',
    )
    context = Context({}, loop=loop)
    q = Queue(config, context=context, loop=loop)
    await q.init()
    async with q:
        await q.put({'f': 3})
        assert 1 == await q.length()
        assert [{'f': 3}] == await q.list()
        assert {'f': 3} == await q.get()
        await q.put({'f': 3})
        assert 1 == await q.length()
        await q.clear()
        assert not await q.length()


async def test_zqueue(loop, mocker):
    config = MergeDict(
        key=str(uuid.uuid4()),
        format='str',
        timeout=0,
    )
    context = Context({}, loop=loop)
    q = ZQueue(config, context=context, loop=loop)
    await q.init()
    async with q:
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

        with pytest.raises(TypeError):
            with mocker.patch('asyncio.sleep'):
                await q.get()


async def test_ts_zqueue(loop, mocker):
    config = MergeDict(
        key=str(uuid.uuid4()),
        format='str',
        timeout=10,
    )
    context = Context({}, loop=loop)
    q = TimestampZQueue(config, context=context, loop=loop)
    await q.init()

    async with q:
        await q.put('c', time.time() + 4)
        await q.put('a', 4)
        assert 2 == await q.length()
        assert ['a', 'c'] == await q.list()
        assert 'a' == await q.get()
        assert 1 == await q.length()
        assert ['c'] == await q.list()

        async def breaker(*args, **kwargs):
            raise InterruptedError

        mocker.patch('asyncio.sleep', breaker)
        with pytest.raises(InterruptedError):
            await q.get()
