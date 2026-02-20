from __future__ import annotations

import asyncio
import time


class AsyncTokenBucket:
    def __init__(self, rps: float, burst: int):
        self.rps = float(rps)
        self.capacity = int(burst)
        self.tokens = float(burst)
        self.last = time.time()
        self._lock = asyncio.Lock()

    async def take(self, amount: float = 1.0) -> None:
        while True:
            async with self._lock:
                now = time.time()
                elapsed = now - self.last
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rps)
                self.last = now
                if self.tokens >= amount:
                    self.tokens -= amount
                    return
            await asyncio.sleep(0.05)
