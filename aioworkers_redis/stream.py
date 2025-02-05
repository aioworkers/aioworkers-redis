import socket
from uuid import uuid4

from aioworkers_redis.base import BaseQueue


class XQueue(BaseQueue):
    def set_config(self, config):
        super().set_config(config)
        hostname = socket.gethostname()
        self._format_fields = frozenset(self.config.get("format_fields") or ())
        self._maxlen = self.config.get("maxlen")
        self._group_name = self.config.get("group_name") or hostname
        self._group_create = self.config.get_bool("group_create", default=True)
        self._consumer_name = self.config.get("consumer_name") or f"{hostname}-{uuid4()}"

    def factory(self, item, config=None):
        inst = super().factory(item, config=config)
        inst._format_fields = self._format_fields
        inst._maxlen = self._maxlen
        inst._group_name = self._group_name
        inst._consumer_name = self._consumer_name
        return inst

    async def connect(self):
        await super().connect()
        if self._group_create:
            await self.create_group(stream=self.key, group_name=self._group_name)

    async def create_group(self, stream: str, group_name: str):
        try:
            await self.adapter.execute(
                "XGROUP",
                "CREATE",
                stream,
                group_name,
                "$",
                "MKSTREAM",
            )
            self.logger.error("Group %r created on stream %r", group_name, stream)
        except Exception as ex:
            self.logger.debug("XGroup create error: %r", ex)

    async def get(self, timeout: float = 0):
        async with self._lock:
            data = await self.adapter.xread(
                self.key,
                id=">",
                count=1,
                noack=False,
                block=timeout,
                group=self._group_name,
            )
        for _stream, items in data.items():
            for _msg_id, item in items.items():
                result = {}
                for k, v in item.items():
                    if not self._format_fields or k in self._format_fields:
                        result[k] = self.decode(v)
                    else:
                        result[k] = v
                return result
        raise TimeoutError

    async def put(self, value):
        fields = {}
        for k, v in value.items():
            if v is None:
                pass
            elif not self._format_fields or k in self._format_fields:
                fields[k] = self.encode(v)
            else:
                fields[k] = v
        kwargs = {}
        if self._maxlen:
            kwargs["maxlen"] = self._maxlen
            kwargs["approx"] = True
        await self.adapter.xadd(
            self.key,
            fields,
            **kwargs,
        )
