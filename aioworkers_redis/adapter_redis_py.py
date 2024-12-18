import logging
from typing import List, Optional, Union

from redis.asyncio import Redis

from aioworkers_redis.adapter import Adapter

logger = logging.getLogger(__name__)


class AdapterRedisPy:
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
            kwargs["max_connections"] = max_size

        self._nodes: List[str] = []
        if isinstance(address, str):
            self._nodes = [address]
        else:
            for n in address:
                if isinstance(n, list):
                    self._nodes.extend(n)
                else:
                    self._nodes.append(n)

        self.client = Redis.from_url(self._nodes[0], **kwargs)
        return self.client  # type: ignore

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()  # type: ignore
