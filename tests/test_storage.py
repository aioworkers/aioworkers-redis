import uuid

import aioredis
from aioworkers.core.config import MergeDict
from aioworkers.core.context import Context
from aioworkers_redis.storage import RedisStorage, FieldStorage


async def test_storage(loop):
    config = MergeDict(
        name='1',
        prefix=str(uuid.uuid4()),
        format='json',
    )
    config['app.redis_pool'] = await aioredis.create_pool(
        ('localhost', 6379), loop=loop)
    context = config
    q = RedisStorage(config, context=context, loop=loop)
    await q.init()
    await q.set('g', {'f': 3})
    assert {'f': 3} == await q.get('g')
    assert 1 == await q.length()
    assert ['g'] == await q.list()
    await q.set('g', None)
    assert not await q.length()


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
    context['app.redis_pool'] = await aioredis.create_pool(
        ('localhost', 6379), loop=loop)
    storage = FieldStorage(config, context=context, loop=loop)
    await storage.init()
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
