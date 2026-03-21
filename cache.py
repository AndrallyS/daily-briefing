"""
cache.py — JSON-based cache of already-seen post IDs.
Committed to the repo so it persists across GitHub Actions runs.
No Redis needed — a simple JSON file is perfect for this scale.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

CACHE_PATH = Path("seen_ids.json")
MAX_CACHE_SIZE = 2000  # keep last N IDs to prevent unbounded growth


def load_seen() -> Set[str]:
    """Load previously seen post IDs."""
    if not CACHE_PATH.exists():
        return set()
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return set(data.get("ids", []))
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("Cache read error: %s — starting fresh", exc)
        return set()


def save_seen(new_ids: Set[str]) -> None:
    """Merge new_ids into existing cache and persist."""
    existing = load_seen()
    merged   = existing | new_ids

    # Trim to last MAX_CACHE_SIZE to prevent unbounded growth
    if len(merged) > MAX_CACHE_SIZE:
        # Keep most recently added (new_ids take priority)
        trimmed = list(new_ids) + [i for i in existing if i not in new_ids]
        merged  = set(trimmed[:MAX_CACHE_SIZE])

    CACHE_PATH.write_text(
        json.dumps({"ids": sorted(merged), "count": len(merged)}, indent=2),
        encoding="utf-8",
    )
    logger.info("Cache updated: %d total IDs", len(merged))


def filter_unseen(items: List[Dict], seen: Set[str]) -> List[Dict]:
    """Remove items whose IDs have already been sent."""
    before = len(items)
    fresh  = [i for i in items if i.get("id") not in seen]
    logger.info("Cache filter: %d → %d items (%d skipped)",
                before, len(fresh), before - len(fresh))
    return fresh


def mark_as_seen(items: List[Dict]) -> None:
    """Persist the IDs of items included in this run."""
    ids = {i["id"] for i in items if i.get("id")}
    save_seen(ids)
