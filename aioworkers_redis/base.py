import asyncio
from typing import Any, Optional, Type, Union

from aioworkers.core.base import AbstractConnector, AbstractNestedEntity, LoggingEntity
from aioworkers.core.config import ValueExtractor
from aioworkers.core.formatter import FormattedEntity
from aioworkers.core.plugin import iter_entry_points
from aioworkers.queue.base import AbstractQueue

from aioworkers_redis.adapter import Adapter, AdapterHolder

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6379

Client = Any


class Connector(
    AbstractNestedEntity,
    AbstractConnector,
    FormattedEntity,
    LoggingEntity,
):
    def __init__(self, *args, **kwargs):
        self._joiner: str = ":"
        self._prefix: str = ""
        self._connector: Optional[Connector] = None
        self._adapter_holder: Optional[AdapterHolder] = None
        self._adapter: Optional[Adapter] = None
        super().__init__(*args, **kwargs)

    def set_config(self, config):
        self._joiner = config.get("joiner", ":")
        self._prefix = config.get("prefix", "")
        cfg = config.new_parent(logger="aioworkers_redis")
        c = cfg.get("connection")
        if not isinstance(c, str):
            if cfg.get("dsn"):
                cfg = cfg.new_child(connection=dict(dsn=cfg.get("dsn")))
        elif c.startswith("redis://"):
            cfg = cfg.new_child(connection=dict(dsn=c))
        elif not c.startswith("."):
            raise ValueError("Connector link must be startswith point .%s" % c)
        super().set_config(cfg)

    @property
    def pool(self) -> Client:
        connector = self._connector or self._get_connector()
        assert connector._adapter_holder is not None, "Client is not ready"
        assert connector._adapter_holder.client is not None, "Client is not ready"
        return connector._adapter_holder.client

    @property
    def adapter(self) -> Adapter:
        connector = self._connector or self._get_connector()
        assert connector._adapter is not None, "Adapter is not ready"
        return connector._adapter

    def _get_connector(self) -> "Connector":
        cfg = self.config.get("connection")
        if isinstance(cfg, str):
            self.logger.debug("Connect to %s", cfg)
            self._connector = self.context.get_object(cfg)
            assert self._connector is not None, "Not found reference %s" % cfg
        else:
            self._connector = self
        return self._connector

    def get_child_config(
        self,
        item: str,
        config: Optional[ValueExtractor] = None,
    ) -> Optional[ValueExtractor]:
        if config is None:
            result = ValueExtractor(
                dict(
                    name=f"{self.config.name}.{item}",
                )
            )
        else:
            result = super().get_child_config(item, config) or ValueExtractor()
        if self._connector is None:
            connection = self.config.get("connection")
            if not isinstance(connection, str):
                connection = f".{self.config.name}"
            result = result.new_parent(
                connection=connection,
            )
        else:
            result = result.new_child(
                connection=f".{self._connector.config.name}",
            )
        assert result is not None
        result = result.new_child(
            prefix=self.raw_key(result.get("prefix", item)),
        )
        return result.new_parent(
            joiner=self._joiner,
            format=self.config.get("format"),
        )

    def raw_key(self, key: str) -> str:
        k = [i for i in (self._prefix, key) if i]
        return self._joiner.join(k)

    def clean_key(self, raw_key: Union[str, bytes]) -> str:
        result = raw_key[len(self._prefix) + len(self._joiner) :]
        if isinstance(result, str):
            return result
        return result.decode()

    async def connect(self):
        connector = self._connector or self._get_connector()
        if connector is not self:
            return

        cfg = self.config.get("connection")

        c = self
        while True:
            if c._connector is not c:
                assert c._connector
                c = c._connector
            else:
                if self.config.get("connect"):
                    self._connector = self
                    cfg = c.config.get("connection")
                break
        if cfg:
            cfg = dict(cfg)
        else:
            cfg = {}

        if entry_point_name := self.config.get("client"):
            cfg.setdefault("client", entry_point_name)
        if entry_point_name := c.config.get("client"):
            cfg.setdefault("client", entry_point_name)

        if cfg.get("dsn"):
            address = cfg.pop("dsn")
        elif cfg.get("address"):
            address = cfg.pop("address")
        else:
            host = cfg.pop("host", DEFAULT_HOST)
            port = cfg.pop("port", DEFAULT_PORT)
            address = "redis://{}:{}".format(host, port)
        if "maxsize" in cfg:
            cfg["max_size"] = cfg.pop("maxsize")

        client_name = cfg.pop("client", None)
        priority = {
            "redis-rs": 888,
            "redis-py": 88,
            "aioredis": 8,
        }
        entry_points = list(iter_entry_points(group="aioworkers_redis", name=client_name))
        entry_points.sort(key=lambda x: priority.get(x.name, 0), reverse=True)
        for p in entry_points:
            try:
                factory: Type[AdapterHolder] = p.load()
            except ImportError as e:
                if client_name:
                    raise ImportError(f"Try loading {client_name}") from e
                else:
                    continue
            else:
                self._adapter_holder = factory(logger=self.logger)
                self.logger.info("Create client with address %s", address)
                self._adapter = await self._adapter_holder.__aenter__(address, **cfg)
                break
        else:
            raise ImportError("Try loading plugins " + ",".join(e.name for e in entry_points))

    async def disconnect(self):
        if adapter := self._adapter_holder:
            self.logger.debug("Close connection")
            await adapter.__aexit__(None, None, None)

    def decode(self, b):
        if b is not None:
            return super().decode(b)

    def encode(self, b):
        if b is not None:
            return super().encode(b)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


class KeyEntity(Connector):
    @property
    def key(self):
        if not hasattr(self, "_key"):
            self._key = self.raw_key(self.config.key)
        return self._key

    def factory(self, item, config=None):
        inst = super().factory(item, config=config)
        inst._prefix = self.raw_key(self.config.key)
        inst._key = inst.raw_key(item)
        return inst


class BaseQueue(KeyEntity, AbstractQueue):
    async def init(self):
        self._lock = asyncio.Lock()
        await super().init()

    def factory(self, item, config=None):
        inst = super().factory(item, config=config)
        inst._lock = asyncio.Lock()
        return inst
