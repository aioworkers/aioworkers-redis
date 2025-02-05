import uuid

import pytest

from aioworkers_redis.stream import XQueue


@pytest.fixture
def config_yaml():
    return """
    q:
        cls: aioworkers_redis.stream.XQueue
        key: xqueue:{uuid}
        group_name: x
        format: json
    """.format(uuid=uuid.uuid4())


async def test_queue(context):
    q: XQueue = context.q

    data = {"a": 3}
    await q.put(data)
    assert data == await q.get()

    data["a"] += 1
    await q.put(data)
    assert data == await q.get()

    data["a"] += 1
    await q.put(data)
    assert data == await q.get()

    with pytest.raises(TimeoutError):
        await q.get(timeout=1)
