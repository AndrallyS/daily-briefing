"""
rss_fetcher.py v2 — RSS/Atom feed fetcher with retry.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def _parse_date(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                import calendar
                return datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
            except Exception:
                pass
    return None


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
def fetch_feed(feed_url: str, category: str, lookback_hours: int = 24) -> List[Dict]:
    cutoff  = datetime.now(tz=timezone.utc) - timedelta(hours=lookback_hours)
    parsed  = feedparser.parse(feed_url, agent="DailyBriefingBot/2.0")
    source  = parsed.feed.get("title", feed_url)[:40]
    articles = []

    for entry in parsed.entries:
        pub = _parse_date(entry)
        if pub and pub < cutoff:
            continue

        title   = (entry.get("title") or "").strip()
        link    = (entry.get("link")  or "").strip()
        summary = re.sub(r"<[^>]+>", "",
                         entry.get("summary") or entry.get("description") or "")[:400]

        if not title or not link:
            continue

        articles.append({
            "id":               entry.get("id", link),
            "title":            title,
            "url":              link,
            "permalink":        link,
            "summary":          summary.strip(),
            "source":           source,
            "created_at":       pub or datetime.now(tz=timezone.utc),
            "category":         category,
            "score":            0,
            "upvote_ratio":     0.5,
            "num_comments":     0,
            "subreddit":        "",
            "author":           entry.get("author", ""),
            "flair":            "article",
            "selftext":         summary.strip(),
            "ai_summary":       "",
            "detected_lang":    "en",
            "title_translated": "",
            "sentiment":        "neutral",
        })

    logger.info("Feed %-45s → %d articles", feed_url[:45], len(articles))
    return articles


def fetch_all_feeds(feed_map: Dict[str, List[str]], lookback_hours: int = 24) -> List[Dict]:
    all_articles: List[Dict] = []
    for category, urls in feed_map.items():
        for url in urls:
            try:
                all_articles.extend(fetch_feed(url, category, lookback_hours))
            except Exception as exc:
                logger.warning("Feed %s failed: %s", url, exc)
            time.sleep(0.3)
    logger.info("Total RSS articles: %d", len(all_articles))
    return all_articles
