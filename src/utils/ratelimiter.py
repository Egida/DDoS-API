from pyrate_limiter import Duration, Rate, Limiter, BucketFullException

limiter = Limiter(Rate(3, Duration.MINUTE))

def ratelimiter(key):
    try:
        limiter.try_acquire(key)
        return True
    except BucketFullException:
        return False