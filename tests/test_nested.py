import pytest


@pytest.fixture
def config_yaml():
    return """
    connector:
      cls: aioworkers_redis.base.Connector
      prefix: a
      b:
        cls: aioworkers_redis.base.Connector
    """


async def test_connect(context):
    assert context.connector.raw_key('3') == 'a:3'
    assert context.connector.b.raw_key('3') == 'a:b:3'
    assert context.connector.clean_key('a:3') == '3'


async def test_connector(context):
    assert context.connector.b.config.connection == '.connector'
    assert context.connector.b.a.config.connection == '.connector'
    assert context.connector.b.a.c.config.connection == '.connector'
    assert context.connector.a.config.connection == '.connector'
    assert context.connector.a.b.config.connection == '.connector'
