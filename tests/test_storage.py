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
    hyperloglog:
        cls: aioworkers_redis.storage.HyperLogLogStorage
        key: hll
    """.format(uuid=uuid.uuid4())


async def test_storage(context):
    s = context.storage
    await s.set("g", {"f": 3})
    assert {"f": 3} == await s.get("g")
    assert 1 == await s.length()
    assert ["g"] == await s.list()
    await s.set("g", None)
    assert not await s.length()


async def test_nested_storage(context):
    s = context.storage
    q_child = s.child
    await q_child.set("1", 1)
    assert q_child.raw_key("1") == s.config.prefix + ":child:1"
    assert 1 == await q_child.get("1")


async def test_expiry_storage(event_loop, config):
    key = "6"
    data = {"f": 3, "g": 4, "h": 5}
    config.update(
        storage=dict(
            expiry=1,
        )
    )
    async with Context(config, loop=event_loop) as ctx:
        await ctx.storage.set(key, data)
        await ctx.storage.expiry(key, 1)


async def test_field_storage(event_loop, config):
    key = "6"
    data = {"f": 3, "g": 4, "h": 5}
    fields = ["f", "g"]
    config.update(
        storage=dict(
            cls="aioworkers_redis.storage.HashStorage",
            expiry=1,
        )
    )
    async with Context(config, loop=event_loop) as ctx:
        storage = ctx.storage
        await storage.set(key, data)
        assert data == await storage.get(key)
        assert 5 == await storage.get(key, field="h")
        await storage.set(key, 6, field="h")
        await storage.set(key, None, field="f")
        assert {"f": None, "g": 4} == await storage.get(key, fields=fields)
        await storage.set(key, {"g": None}, fields=["g"])
        await storage.set(key, {"z": 1, "y": 6}, fields=["z"])
        assert {"h": 6, "z": 1} == await storage.get(key)
        await storage.set(key, None)


async def test_hyperloglog(context):
    hll = context.hyperloglog
    await hll.set("a", True)
    assert True is await hll.get("a")
    assert False is await hll.get("b")
    assert False is await hll.get("b")
    assert True is await hll.get("a")
    assert 1 == await hll.length()
