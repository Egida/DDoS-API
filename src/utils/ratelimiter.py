from pyrate_limiter import Limiter, Rate
from asyncer import asyncify

limiter = Limiter(Rate(5, 60))

async def ratelimiter(key):
    try:
        await asyncify(limiter.try_acquire)(key)
        return True
    except:
        return False