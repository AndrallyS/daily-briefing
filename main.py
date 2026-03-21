"""
main.py — Daily Briefing Bot v3 orchestrator.

Modes:
  python main.py daily    — Full briefing (all 5 categories)
  python main.py alert    — Breaking news scan (silent if nothing critical)

Categories: gaming · gamedev · ai · tech · br
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("briefing.main")

import config
from reddit_fetcher import fetch_all_posts
from rss_fetcher    import fetch_all_feeds
from ranker         import build_ranked_briefing, check_critical_alerts
from ai_summarizer  import enrich_items
from html_renderer  import render_html, render_plaintext
from notifier       import dispatch
from cache          import load_seen, filter_unseen, mark_as_seen
from storage        import save_run


# ─────────────────────────────────────────────────────────────
# Daily briefing — all categories
# ─────────────────────────────────────────────────────────────

def run_daily() -> None:
    start = time.time()
    logger.info("=" * 62)
    logger.info("🚀  Daily Briefing Bot v3 — starting daily run")
    logger.info("=" * 62)

    seen = load_seen()
    logger.info("Cache: %d known post IDs", len(seen))

    # Subreddit map — only enabled categories
    all_subreddit_map = {
        "gaming":  config.GAMING_SUBREDDITS,
        "gamedev": config.GAMEDEV_SUBREDDITS,
        "ai":      config.AI_SUBREDDITS,
        "tech":    config.TECH_SUBREDDITS,
        "br":      config.BR_SUBREDDITS,
    }
    subreddit_map = {k: v for k, v in all_subreddit_map.items()
                     if k in config.ENABLED_CATEGORIES}

    # RSS feed map — only enabled categories
    all_feed_map = {
        "gaming":  config.GAMING_RSS_FEEDS,
        "gamedev": config.GAMEDEV_RSS_FEEDS,
        "ai":      config.AI_RSS_FEEDS,
        "tech":    config.TECH_RSS_FEEDS,
    }
    feed_map = {k: v for k, v in all_feed_map.items()
                if k in config.ENABLED_CATEGORIES}

    logger.info("📡  Fetching Reddit posts…")
    reddit_posts = fetch_all_posts(
        subreddit_map=subreddit_map,
        posts_per_sub=config.POSTS_PER_SUBREDDIT,
        lookback_hours=config.LOOKBACK_HOURS,
        min_score=config.MIN_SCORE,
    )

    logger.info("📰  Fetching RSS articles…")
    rss_articles = fetch_all_feeds(
        feed_map=feed_map,
        lookback_hours=config.LOOKBACK_HOURS,
    )

    all_items = reddit_posts + rss_articles
    logger.info("Collected: %d Reddit posts + %d RSS articles = %d total",
                len(reddit_posts), len(rss_articles), len(all_items))

    if not all_items:
        logger.warning("No items collected — aborting.")
        sys.exit(0)

    fresh = filter_unseen(all_items, seen)

    logger.info("🏆  Ranking…")
    briefing = build_ranked_briefing(
        items=fresh,
        top_n=config.MAX_POSTS_IN_REPORT,
    )

    logger.info("🤖  Enriching with AI…")
    all_enriched = []
    for cat, items in briefing.items():
        enriched = enrich_items(items)
        briefing[cat] = enriched
        all_enriched.extend(enriched)
        logger.info("  [%-8s] %d items", cat.upper(), len(enriched))
        for i, item in enumerate(enriched, 1):
            logger.info("    #%d (%.1f) %s",
                        i, item.get("relevance_score", 0), item["title"][:65])

    logger.info("🎨  Rendering HTML…")
    html_body  = render_html(briefing)
    plain_body = render_plaintext(briefing)

    Path("docs").mkdir(exist_ok=True)
    Path("docs/index.html").write_text(html_body, encoding="utf-8")

    logger.info("🗄️   Saving to SQLite…")
    save_run(briefing, mode="daily", duration_sec=time.time() - start)

    mark_as_seen(all_enriched)

    logger.info("📤  Dispatching notifications…")
    results = dispatch(briefing, html_body=html_body, plain_body=plain_body, mode="daily")
    for channel, ok in results.items():
        logger.info("  %s  %s", "✅" if ok else "❌", channel)

    if not results:
        logger.warning("⚠️  No notification channel configured!")
        logger.warning("    Set at least one of: TELEGRAM_BOT_TOKEN, DISCORD_WEBHOOK_URL, SMTP_USER")

    elapsed = time.time() - start
    logger.info("=" * 62)
    logger.info("🏁  Done in %.1fs", elapsed)
    logger.info("=" * 62)


# ─────────────────────────────────────────────────────────────
# Alert scan — once per day, silent if nothing critical
# ─────────────────────────────────────────────────────────────

def run_alert() -> None:
    logger.info("=" * 62)
    logger.info("🚨  Daily Alert Scan — starting")
    logger.info("=" * 62)

    reddit_posts = fetch_all_posts(
        subreddit_map={
            "gaming":  config.GAMING_SUBREDDITS,
            "gamedev": config.GAMEDEV_SUBREDDITS,
            "ai":      config.AI_SUBREDDITS,
            "tech":    config.TECH_SUBREDDITS,
        },
        posts_per_sub=20,
        lookback_hours=config.ALERT_LOOKBACK_HOURS,
        min_score=config.ALERT_MIN_SCORE // 3,
    )

    alerts = check_critical_alerts(reddit_posts, min_score=config.ALERT_MIN_SCORE)

    if not alerts:
        logger.info("✅  No critical alerts found. Staying silent.")
        return

    logger.info("🚨  %d critical alert(s) found!", len(alerts))

    alerts = enrich_items(alerts)

    alert_briefing: dict = {cat: [] for cat in config.CATEGORY_META}
    for item in alerts:
        cat = item.get("category", "tech")
        if cat in alert_briefing:
            alert_briefing[cat].append(item)
    alert_briefing = {k: v for k, v in alert_briefing.items() if v}

    dispatch(alert_briefing, mode="alert")
    save_run(alert_briefing, mode="alert")

    logger.info("🏁  Alert scan done.")


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "daily"
    if mode == "alert":
        run_alert()
    else:
        run_daily()
