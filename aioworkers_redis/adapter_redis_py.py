import logging
from typing import Dict, List, Optional, Union
from uuid import uuid4

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
        self.client_id = str(uuid4())

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
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()  # type: ignore

    def __getattr__(self, name):
        return getattr(self.client, name)

    async def execute(self, *args):
        return await self.client.execute_command(*args)

    async def blpop(self, *keys, timeout: float) -> Dict:
        result = await self.client.blpop(*keys, timeout=timeout)
        if result:
            k, v = result
            return {k.decode("UTF-8"): v}
        return {}

    async def xadd(self, *args, **kwargs):
        result = await self.client.xadd(*args, **kwargs)
        if result:
            return result.decode("UTF-8")

    async def xread(
        self,
        *streams: str,
        id: str,
        block: Optional[int] = None,
        count: Optional[int] = None,
        noack: Optional[bool] = None,
        group: Optional[str] = None,
    ) -> Dict:
        if group:
            data = await self.client.xreadgroup(
                streams={stream: ">" for stream in streams},
                groupname=group,
                consumername=self.client_id,
                block=block,
                count=count,
                noack=noack or False,
            )
        else:
            data = await self.client.xread(
                streams={s: id for s in streams},
                block=block,
                count=count,
            )
        result: dict = {}
        for streamb, msgs in data:
            stream = result.setdefault(streamb.decode("UTF-8"), {})
            for msg_id, msgb in msgs:
                msg = {k.decode("UTF-8"): v for k, v in msgb.items()}
                stream[msg_id.decode("UTF-8")] = msg
        return result
