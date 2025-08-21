import asyncio
import time
from urllib.parse import urlparse
from collections import defaultdict
from typing import Dict, Optional

from app.config import settings

class DomainLimiter:
    def __init__(self, max_concurrent_per_domain: int = None):
        self.max_concurrent_per_domain = max_concurrent_per_domain or settings.MAX_CONCURRENT_REQUESTS_PER_DOMAIN
        self.domain_semaphores = defaultdict(lambda: asyncio.Semaphore(self.max_concurrent_per_domain))
        self.active_requests = defaultdict(int)
        self.total_requests = defaultdict(int)
        self.wait_times = defaultdict(list)
    
    def get_domain(self, url: str) -> str:
        """Извлекает домен из URL"""
        return urlparse(url).netloc
    
    def get_domain_semaphore(self, url: str) -> asyncio.Semaphore:
        domain = self.get_domain(url)
        return self.domain_semaphores[domain]

    async def acquire(self, url: str) -> asyncio.Semaphore:
        domain = self.get_domain(url)
        semaphore = self.get_domain_semaphore(url)
    
        start_wait = time.time()
        
        print(f"🔒 Domain limiter: Requesting access to {domain} "
              f"(active: {self.active_requests[domain]}/{self.max_concurrent_per_domain})")
        
        await semaphore.acquire()
        
        wait_time = time.time() - start_wait
        self.wait_times[domain].append(wait_time)
        self.active_requests[domain] += 1
        self.total_requests[domain] += 1
        
        if wait_time > 0.1:
            print(f"⏰ Domain limiter: Waited {wait_time:.2f}s for {domain}")
        
        print(f"✅ Domain limiter: Access granted to {domain} "
              f"(active: {self.active_requests[domain]}/{self.max_concurrent_per_domain})")
        
        return semaphore

    async def release(self, url: str) -> None:
        domain = self.get_domain(url)
        semaphore = self.get_domain_semaphore(url)
        semaphore.release()
        
        self.active_requests[domain] = max(0, self.active_requests[domain] - 1)
        
        print(f"🔓 Domain limiter: Released access to {domain} "
              f"(active: {self.active_requests[domain]}/{self.max_concurrent_per_domain})")

    def get_stats(self) -> Dict:
        """Возвращает статистику по доменам"""
        stats = {}
        for domain in set(list(self.active_requests.keys()) + list(self.total_requests.keys())):
            wait_times = self.wait_times[domain]
            stats[domain] = {
                "active_requests": self.active_requests[domain],
                "total_requests": self.total_requests[domain],
                "max_concurrent": self.max_concurrent_per_domain,
                "avg_wait_time": sum(wait_times) / len(wait_times) if wait_times else 0,
                "max_wait_time": max(wait_times) if wait_times else 0
            }
        return stats

domain_limiter = DomainLimiter()