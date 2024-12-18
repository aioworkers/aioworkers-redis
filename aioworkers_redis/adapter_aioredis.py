import logging
from typing import Any, List, Optional, Union

from aioredis import Redis, create_redis_pool

from aioworkers_redis.adapter import Adapter

logger = logging.getLogger(__name__)


class AdapterAioRedis:
    client: Redis

    def __init__(
        self,
        logger: logging.Logger = logger,
    ) -> None:
        self.logger = logger

    async def __aenter__(
        self,
        address: Union[str, List[str], List[List[str]]] = "redis://localhost:6379",
        db: Optional[int] = None,
        max_size: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> Adapter:
        self.logger = logger or self.logger

        kwargs.clear()
        if db is not None:
            kwargs["db"] = db
        if max_size is not None:
            kwargs["maxsize"] = max_size

        nodes: List[str] = []
        if isinstance(address, str):
            nodes = [address]
        else:
            for n in address:
                if isinstance(n, list):
                    nodes.extend(n)
                else:
                    nodes.append(n)

        self.client = await create_redis_pool(nodes[0], **kwargs)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        await self.client.wait_closed()

    def __getattr__(self, name):
        return getattr(self.client, name)

    def eval(self, script: str, n: int, *args) -> Any:
        keys = args[:n]
        args = args[n:]
        return self.client.eval(script, keys=keys, args=args)

    def zadd(self, key: str, mapping: dict) -> Any:
        args = []
        for f, score in mapping.items():
            args.extend([score, f])
        return self.client.zadd(key, *args)

    def hset(self, key: str, *pairs, mapping: Optional[dict] = None) -> Any:
        args = []
        if mapping:
            for f, v in mapping.items():
                args.extend([f, v])
        return self.client.hmset(key, *pairs, *args)

    def set(self, key: str, value: Any, *, ex: Optional[int] = None) -> Any:
        if ex:
            return self.client.setex(key, ex, value)
        else:
            return self.client.set(key, value)