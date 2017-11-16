from aioworkers.core.config import MergeDict
from aioworkers.core.context import Context
from aioworkers_redis.base import Connector


async def test_connect(loop):
    context = Context({}, loop=loop)
    config = MergeDict(prefix='1')
    q = Connector(config, context=context, loop=loop)
    context.connector = q
    await q.init()
    async with q:
        pass

    config = MergeDict(connection='connector', prefix='2')
    q = Connector(config, context=context, loop=loop)
    await q.init()
    async with q:
        assert q.raw_key('3') == '1:2:3'
        assert q.clean_key('1:2:3') == '3'
