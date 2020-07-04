import pytest


@pytest.fixture
def config_yaml():
    return """
    connector:
      cls: aioworkers_redis.base.Connector
      prefix: a
      b:
        cls: aioworkers_redis.base.Connector
      c:
        prefix: z
    """


async def test_connect(context):
    assert context.connector.raw_key('3') == 'a:3'
    assert context.connector.b.raw_key('3') == 'a:b:3'
    assert context.connector.clean_key('a:3') == '3'


def test_child_prefix(context):
    c = context.connector
    assert c.raw_key('b:x') == c.b.raw_key('x')
    assert c.raw_key('z:x') == c.c.raw_key('x')


async def test_connector(context):
    assert context.connector.b.config.connection == '.connector'
    assert context.connector.b.a.config.connection == '.connector'
    assert context.connector.b.a.c.config.connection == '.connector'
    assert context.connector.a.config.connection == '.connector'
    assert context.connector.a.b.config.connection == '.connector'
