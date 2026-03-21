"""
reddit_fetcher.py v3.1 — Public Reddit JSON API.
No app registration, no credentials, no PRAW required.
Uses reddit.com/{subreddit}/hot.json like a regular browser request.
Rate limit: ~60 requests/minute — well within our usage.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

import config

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DailyBriefingBot/3.1; +https://github.com/daily-briefing)",
    "Accept": "application/json",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def _make_post(raw: dict, category: str) -> Dict:
    data = raw.get("data", {})
    created_utc = data.get("created_utc", time.time())
    selftext = (data.get("selftext") or "")[:500]
    if selftext in ("[deleted]", "[removed]"):
        selftext = ""

    return {
        "id":               data.get("id", ""),
        "title":            data.get("title", ""),
        "url":              data.get("url", ""),
        "permalink":        f"https://reddit.com{data.get('permalink', '')}",
        "score":            data.get("score", 0),
        "upvote_ratio":     data.get("upvote_ratio", 0.5),
        "num_comments":     data.get("num_comments", 0),
        "subreddit":        data.get("subreddit", ""),
        "author":           data.get("author", "[deleted]"),
        "created_at":       datetime.fromtimestamp(created_utc, tz=timezone.utc),
        "selftext":         selftext,
        "flair":            data.get("link_flair_text") or "",
        "category":         category,
        "source":           "reddit",
        "ai_summary":       "",
        "detected_lang":    "en",
        "title_translated": "",
        "sentiment":        "neutral",
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _fetch_one(subreddit: str, category: str, limit: int,
               cutoff: datetime, min_score: int) -> List[Dict]:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    params = {"limit": min(limit, 100), "raw_json": 1}

    try:
        resp = SESSION.get(url, params=params, timeout=15)

        if resp.status_code == 404:
            logger.warning("r/%s — not found (404), skipping", subreddit)
            return []
        if resp.status_code == 403:
            logger.warning("r/%s — private (403), skipping", subreddit)
            return []
        if resp.status_code == 429:
            logger.warning("r/%s — rate limited, waiting 10s", subreddit)
            time.sleep(10)
            return []

        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])

    except requests.RequestException as exc:
        logger.warning("r/%s — request error: %s", subreddit, exc)
        return []

    posts = []
    for child in children:
        if child.get("kind") != "t3":
            continue
        post = _make_post(child, category)
        stickied = child.get("data", {}).get("stickied", False)
        if stickied or post["created_at"] < cutoff or post["score"] < min_score:
            continue
        posts.append(post)

    logger.info("r/%-24s → %d posts", subreddit, len(posts))
    return posts


def fetch_all_posts(
    subreddit_map: Dict[str, List[str]],
    posts_per_sub: int = 15,
    lookback_hours: int = 24,
    min_score: int = 50,
) -> List[Dict]:
    cutoff    = datetime.now(tz=timezone.utc) - timedelta(hours=lookback_hours)
    all_posts: List[Dict] = []

    for category, subreddits in subreddit_map.items():
        for sub in subreddits:
            posts = _fetch_one(
                subreddit=sub,
                category=category,
                limit=posts_per_sub + 10,
                cutoff=cutoff,
                min_score=min_score,
            )
            all_posts.extend(posts)
            time.sleep(0.5)

    logger.info("Total Reddit posts collected: %d", len(all_posts))
    return all_posts
