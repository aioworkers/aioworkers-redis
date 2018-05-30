import asyncio


async def run(worker, *args, **kwargs):
    worker.logger.info(args)
    await asyncio.sleep(1)
    return worker.name
