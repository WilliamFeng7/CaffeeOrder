"""Menu listing + cache.

Moved out of `endpoints/menu.py` so that `endpoints/admin.py` can invalidate the
cache without importing from a sibling *router* module, and so that stock changes
made by the order service can bust the cache through one obvious function.

Cache correctness note
----------------------
The cached rows include `inventory_count`, so any mutation that changes stock or
product visibility MUST call `invalidate()`. Previously only the admin product
endpoints did, so an order could leave a sold-out product looking in-stock for up
to `CACHE_TTL` seconds.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import MenuItem

_menu_cache: dict[str, Any] = {"data": None, "timestamp": 0.0}
CACHE_TTL = 300  # seconds


def invalidate() -> None:
    """Drop the cached menu. Call after any stock/visibility change."""
    _menu_cache["data"] = None
    _menu_cache["timestamp"] = 0.0


async def list_active(session: AsyncSession) -> list[MenuItem]:
    """
    Return active menu items, using the in-process cache when fresh.

    The cache is deliberately keyed on nothing but "the public menu": there is
    only one public listing shape in this app.
    """
    cached: Optional[list[MenuItem]] = _menu_cache["data"]
    if cached is not None and (time.time() - _menu_cache["timestamp"]) < CACHE_TTL:
        return cached

    result = await session.exec(select(MenuItem).where(MenuItem.is_active))
    items = list(result.all())

    _menu_cache["data"] = items
    _menu_cache["timestamp"] = time.time()
    return items
