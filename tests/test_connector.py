import pytest
from aioworkers.utils import import_name


@pytest.fixture
def config_yaml():
    return """
    connector:
      cls: aioworkers_redis.base.Connector
      prefix: a
    """


async def test_connect(context):
    assert context.connector.raw_key('3') == 'a:3'
    assert context.connector.b.raw_key('3') == 'a:b:3'
    assert context.connector['b'].raw_key('3') == 'a:b:3'
    assert context.connector['b']['c'].raw_key('3') == 'a:b:c:3'
    assert context.connector['c'].raw_key('3') == 'a:c:3'
    assert context.connector.clean_key('a:3') == '3'


async def test_dsn(config):
    config.update({
        'connector.dsn': 'redis://localhost',
        'connector.name': 'connector',
    })
    cls = import_name(config.connector.cls)
    async with cls(config.connector) as c:
        assert c.connector


async def test_uri(config):
    config.update({
        'connector.connection': 'redis://localhost',
        'connector.name': 'connector',
    })
    cls = import_name(config.connector.cls)
    async with cls(config.connector) as c:
        assert c.connector


async def test_address(config):
    config.update({
        'connector.connection.address': 'redis://localhost',
        'connector.name': 'connector',
    })
    cls = import_name(config.connector.cls)
    async with cls(config.connector) as c:
        assert c.connector


async def test_link(config, mocker):
    config.update({
        'connector.connection': '.connector',
        'connector.name': 'connector',
    })
    cls = import_name(config.connector.cls)
    async with cls(config.connector, context=mocker.Mock()) as c:
        assert c.connector


async def test_bad_link(config):
    config.update({
        'connector.connection': 'redis',
        'connector.name': 'connector',
    })
    cls = import_name(config.connector.cls)
    with pytest.raises(ValueError):
        async with cls(config.connector) as c:
            assert c.connector
