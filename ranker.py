"""
ranker.py v3 — Relevance scoring, sentiment, and alert detection.
Supports 5 categories: gaming, gamedev, ai, tech, br.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import config

logger = logging.getLogger(__name__)
_vader = SentimentIntensityAnalyzer()


def get_sentiment(text: str) -> str:
    s = _vader.polarity_scores(text)["compound"]
    if s >= 0.05:  return "positive"
    if s <= -0.05: return "negative"
    return "neutral"


def _score_upvotes(n: int) -> float:
    return min(35.0, math.log10(n + 1) * 10) if n > 0 else 0.0

def _score_comments(n: int) -> float:
    return min(15.0, math.log10(n + 1) * 5) if n > 0 else 0.0

def _score_ratio(r: float) -> float:
    return 10.0 if r >= 0.95 else 7.0 if r >= 0.85 else 4.0 if r >= 0.70 else 1.0

def _score_keywords(title: str, body: str, flair: str) -> Tuple[float, List[str]]:
    combined = f"{title} {body} {flair}".lower()
    matches  = [kw for kw in config.HIGH_SIGNAL_KEYWORDS if kw.lower() in combined]
    return min(25.0, len(matches) * 6.0), matches

def _score_recency(created: datetime) -> float:
    age = (datetime.now(tz=timezone.utc) - created).total_seconds() / 3600
    return 15.0 if age < 2 else 12.0 if age < 6 else 8.0 if age < 12 else 4.0 if age < 24 else 0.0


def rank_item(item: Dict) -> Dict:
    v = _score_upvotes(item.get("score", 0))
    c = _score_comments(item.get("num_comments", 0))
    r = _score_ratio(item.get("upvote_ratio", 0.5))
    k, kws = _score_keywords(
        item.get("title", ""),
        item.get("selftext") or item.get("summary", ""),
        item.get("flair", ""),
    )
    t = _score_recency(item.get("created_at", datetime.now(tz=timezone.utc)))

    item["relevance_score"]  = round(v + c + r + k + t, 2)
    item["matched_keywords"] = kws
    item["sentiment"]        = get_sentiment(item.get("title", ""))
    return item


def rank_and_select(items: List[Dict], top_n: int, category: str) -> List[Dict]:
    subset = [i for i in items if i.get("category") == category]
    scored = [rank_item(i) for i in subset]

    seen: set = set()
    deduped: List[Dict] = []
    for item in scored:
        key = item["title"].lower()[:60].strip()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    ranked = sorted(deduped, key=lambda x: x["relevance_score"], reverse=True)
    logger.info("  %-8s → %d candidates → top %d selected",
                category.upper(), len(ranked), min(top_n, len(ranked)))
    return ranked[:top_n]


def build_ranked_briefing(items: List[Dict], top_n: int = 5) -> Dict[str, List[Dict]]:
    return {cat: rank_and_select(items, top_n, cat) for cat in config.CATEGORY_META}


def check_critical_alerts(items: List[Dict], min_score: int) -> List[Dict]:
    alerts = []
    for item in items:
        combined = f"{item.get('title','')} {item.get('selftext','')}".lower()
        if (any(kw.lower() in combined for kw in config.CRITICAL_ALERT_KEYWORDS)
                and item.get("score", 0) >= min_score):
            alerts.append(rank_item(item))
    return sorted(alerts, key=lambda x: x.get("relevance_score", 0), reverse=True)[:5]
