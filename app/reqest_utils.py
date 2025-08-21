import asyncio
import aiohttp
from app.config import settings
import random
from app.domain_limiter import domain_limiter


async def make_request(url: str, session: aiohttp.ClientSession, retry_count: int = 0):
    headers = {
        "User-Agent": random.choice(settings.USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    await domain_limiter.acquire(url)

    try:
        await asyncio.sleep(settings.REQUEST_DELAY + random.uniform(0, 1))
        
        proxy = random.choice(settings.PROXIES) if settings.PROXIES else None
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
            if response.status == 403:
                raise Exception("Access forbidden (403)")
            elif response.status == 429:
                raise Exception("Rate limited (429)")
            elif response.status >= 400:
                raise Exception(f"HTTP error {response.status}")
            
            return await response.text()
    except Exception as e:
        if "Access forbidden (403)" in str(e):
            raise e
            
        if retry_count < settings.MAX_RETRIES:
            retry_delay = (settings.RETRY_BACKOFF ** retry_count) * 2
            print(f"Retry {retry_count + 1}/{settings.MAX_RETRIES} after {retry_delay}s for {url}")
            await asyncio.sleep(retry_delay)
            return await make_request(url, session, retry_count + 1)
        raise e
    finally:
        await domain_limiter.release(url)
        