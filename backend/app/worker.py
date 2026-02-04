import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("worker")


async def run():
    from app.jobs.handlers import register_all
    from app.jobs.runner import run_loop

    register_all()
    await run_loop()


if __name__ == "__main__":
    asyncio.run(run())
