from aioworkers.core.formatter import FormattedEntity


class RedisPool(FormattedEntity):
    @property
    def pool(self):
        key_pool = self.config.get('pool', 'redis_pool')
        return self.context.app[key_pool].get()

    def decode(self, b):
        if b is not None:
            return super().decode(b)

    def encode(self, b):
        if b is not None:
            return super().encode(b)
