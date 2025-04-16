import time
from typing import Callable
import functools
import asyncio
import structlog
from app.config.settings import settings

logger = structlog.get_logger("analisaai-sync")

class RateLimiter:
    """Rate limiter to prevent API abuse"""
    
    def __init__(self, rate_limit: int = None):
        """
        Initialize rate limiter
        
        Args:
            rate_limit (int, optional): Max number of requests per second. 
                                       Defaults to settings.RATE_LIMIT_PER_SECOND.
        """
        self.rate_limit = rate_limit or settings.RATE_LIMIT_PER_SECOND
        self.last_request_time = 0
        self._lock = asyncio.Lock()
        
    async def wait(self) -> None:
        """
        Wait to respect rate limit
        """
        async with self._lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            # If we're making requests too quickly, wait
            if time_since_last_request < (1.0 / self.rate_limit):
                sleep_time = (1.0 / self.rate_limit) - time_since_last_request
                logger.debug(f"Rate limiting applied. Waiting {sleep_time:.4f}s")
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = time.time()

def rate_limited(func: Callable) -> Callable:
    """
    Decorator for rate-limited functions
    
    Args:
        func (Callable): Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    # Create a rate limiter instance for this function
    limiter = RateLimiter()
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Wait to respect rate limit
        await limiter.wait()
        
        # Call the original function
        return await func(*args, **kwargs)
        
    return wrapper