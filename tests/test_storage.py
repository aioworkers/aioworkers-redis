import uuid

from aioworkers.core.config import MergeDict
from aioworkers.core.context import Context
from aioworkers_redis.storage import Storage, HashStorage


async def test_storage(loop):
    config = MergeDict(
        name='1',
        prefix=str(uuid.uuid4()),
        format='json',
    )
    context = Context({}, loop=loop)

    q = Storage(config, context=context, loop=loop)
    await q.init()
    async with q:
        await q.set('g', {'f': 3})
        assert {'f': 3} == await q.get('g')
        assert 1 == await q.length()
        assert ['g'] == await q.list()
        await q.set('g', None)
        assert not await q.length()


async def test_nested_storage(loop):
    config = MergeDict(name='1', prefix=str(uuid.uuid4()), format='json')
    context = Context({}, loop=loop)
    q = Storage(config, context=context, loop=loop)
    await q.init()
    async with q:
        q_child = q.child
        await q_child.set('1', 1)
        assert q_child.raw_key('1') == config.prefix + ':child:1'
        assert 1 == await q_child.get('1')


async def test_field_storage(loop):
    key = '6'
    data = {'f': 3, 'g': 4, 'h': 5}
    fields = ['f', 'g']
    config = MergeDict(
        name='',
        prefix=str(uuid.uuid4()),
        format='json',
    )
    context = Context({}, loop=loop)
    storage = HashStorage(config, context=context, loop=loop)
    await storage.init()
    async with storage:
        await storage.set(key, data)
        assert data == await storage.get(key)
        assert 5 == await storage.get(key, field='h')
        await storage.set(key, 6, field='h')
        await storage.set(key, None, field='f')
        assert {'f': None, 'g': 4} == await storage.get(key, fields=fields)
        await storage.set(key, {'g': None}, fields=['g'])
        await storage.set(key, {'z': 1, 'y': 6}, fields=['z'])
        assert {'h': 6, 'z': 1} == await storage.get(key)
        await storage.set(key, None)
