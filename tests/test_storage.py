import uuid

import pytest
from aioworkers.core.context import Context


@pytest.fixture
def config_yaml():
    return """
    storage:
        cls: aioworkers_redis.storage.Storage
        prefix: {uuid}
        format: json
    """.format(uuid=uuid.uuid4())


async def test_storage(context):
    s = context.storage
    await s.set('g', {'f': 3})
    assert {'f': 3} == await s.get('g')
    assert 1 == await s.length()
    assert ['g'] == await s.list()
    await s.set('g', None)
    assert not await s.length()


async def test_nested_storage(context):
    s = context.storage
    q_child = s.child
    await q_child.set('1', 1)
    assert q_child.raw_key('1') == s.config.prefix + ':child:1'
    assert 1 == await q_child.get('1')


async def test_field_storage(loop, config):
    key = '6'
    data = {'f': 3, 'g': 4, 'h': 5}
    fields = ['f', 'g']
    config.update(storage=dict(cls='aioworkers_redis.storage.HashStorage'))
    async with Context(config, loop=loop) as ctx:
        storage = ctx.storage
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
