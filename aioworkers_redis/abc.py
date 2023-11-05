from abc import abstractmethod


class AbsConnector:
    @classmethod
    @abstractmethod
    async def create(cls, **kwargs):
        pass
