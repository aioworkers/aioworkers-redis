import uuid

import aioredis
from aioworkers.core.config import MergeDict
from aioworkers_redis.storage import RedisStorage


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
