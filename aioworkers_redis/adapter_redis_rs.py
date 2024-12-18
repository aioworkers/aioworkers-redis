import logging
from typing import List, Optional, Union

import redis_rs

from aioworkers_redis.adapter import Adapter

logger = logging.getLogger(__name__)


class AdapterRedisRS:
    client: redis_rs.AsyncClient

    def __init__(
        self,
        logger: logging.Logger = logger,
    ):
        self.logger = logger

    async def __aenter__(
        self,
        address: Union[str, List[str], List[List[str]]] = "redis://localhost:6379",
        db: Optional[int] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        cluster: Optional[bool] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        format: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> Adapter:
        self.logger = logger or self.logger
        self._format = format

        kwargs.clear()
        if db is not None:
            kwargs["db"] = db
        if max_size is not None:
            kwargs["max_size"] = max_size
        if cluster is not None:
            kwargs["cluster"] = cluster
        if username is not None:
            kwargs["username"] = username
        if password is not None:
            kwargs["password"] = password
        if client_id is not None:
            kwargs["client_id"] = client_id

        nodes = [address] if isinstance(address, str) else address
        self._client = redis_rs.create_client(*nodes, **kwargs)
        self.client = await self._client.__aenter__()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.__aexit__(exc_type, exc_val, exc_tb)
