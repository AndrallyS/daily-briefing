"""
storage.py — SQLite history. Persisted via GitHub Actions cache.
Tracks every run so you can see trends over time.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

DB_PATH = Path("briefing.db")


# ─────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────

def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date         TEXT    NOT NULL,
            run_ts           TEXT    NOT NULL,
            mode             TEXT    NOT NULL DEFAULT 'daily',
            category         TEXT,
            post_id          TEXT,
            title            TEXT,
            url              TEXT,
            subreddit        TEXT,
            source           TEXT,
            reddit_score     INTEGER DEFAULT 0,
            num_comments     INTEGER DEFAULT 0,
            relevance_score  REAL    DEFAULT 0,
            matched_keywords TEXT,
            sentiment        TEXT,
            rank             INTEGER
        );

        CREATE TABLE IF NOT EXISTS run_meta (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date     TEXT NOT NULL,
            mode         TEXT NOT NULL,
            total_items  INTEGER,
            gaming_count INTEGER,
            tech_count   INTEGER,
            duration_sec REAL
        );

        CREATE INDEX IF NOT EXISTS idx_run_date ON runs(run_date);
        CREATE INDEX IF NOT EXISTS idx_post_id  ON runs(post_id);
    """)
    conn.commit()
    return conn


def save_run(briefing: Dict[str, List[Dict]], mode: str = "daily",
             duration_sec: float = 0.0) -> None:
    """Persist all ranked items from one run."""
    conn = init_db()
    run_ts   = datetime.now(tz=timezone.utc).isoformat()
    run_date = run_ts[:10]

    try:
        for category, items in briefing.items():
            for rank, item in enumerate(items, 1):
                conn.execute("""
                    INSERT INTO runs
                        (run_date, run_ts, mode, category, post_id, title, url,
                         subreddit, source, reddit_score, num_comments,
                         relevance_score, matched_keywords, sentiment, rank)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    run_date, run_ts, mode, category,
                    item.get("id", ""),
                    item.get("title", ""),
                    item.get("url", ""),
                    item.get("subreddit", ""),
                    item.get("source", ""),
                    item.get("score", 0),
                    item.get("num_comments", 0),
                    item.get("relevance_score", 0),
                    json.dumps(item.get("matched_keywords", [])),
                    item.get("sentiment", "neutral"),
                    rank,
                ))

        total = sum(len(v) for v in briefing.values())
        conn.execute("""
            INSERT INTO run_meta
                (run_date, mode, total_items, gaming_count, tech_count, duration_sec)
            VALUES (?,?,?,?,?,?)
        """, (
            run_date, mode, total,
            len(briefing.get("gaming", [])),
            len(briefing.get("tech", [])),
            round(duration_sec, 2),
        ))

        conn.commit()
        logger.info("Saved %d items to SQLite (mode=%s)", total, mode)

    except sqlite3.Error as exc:
        logger.error("DB write error: %s", exc)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# Stats for the HTML dashboard section
# ─────────────────────────────────────────────

def get_stats(days: int = 30) -> Dict:
    """Return aggregated stats for the last N days."""
    if not DB_PATH.exists():
        return {}

    conn = init_db()
    try:
        # Top subreddits
        top_subs = conn.execute("""
            SELECT subreddit, COUNT(*) as c
            FROM runs
            WHERE subreddit != '' AND run_date >= date('now', ?)
            GROUP BY subreddit ORDER BY c DESC LIMIT 8
        """, (f"-{days} days",)).fetchall()

        # Top keywords
        kw_rows = conn.execute("""
            SELECT matched_keywords FROM runs
            WHERE run_date >= date('now', ?)
            AND matched_keywords != '[]'
        """, (f"-{days} days",)).fetchall()

        kw_counts: Dict[str, int] = {}
        for (raw,) in kw_rows:
            for kw in json.loads(raw):
                kw_counts[kw] = kw_counts.get(kw, 0) + 1
        top_kw = sorted(kw_counts.items(), key=lambda x: x[1], reverse=True)[:8]

        # Daily run counts (last 14 days)
        daily = conn.execute("""
            SELECT run_date, COUNT(*) as c
            FROM runs WHERE run_date >= date('now', '-14 days')
            GROUP BY run_date ORDER BY run_date
        """).fetchall()

        total_runs = conn.execute(
            "SELECT COUNT(DISTINCT run_date) FROM run_meta WHERE mode='daily'"
        ).fetchone()[0]

        return {
            "top_subreddits": top_subs,
            "top_keywords":   top_kw,
            "daily_counts":   daily,
            "total_runs":     total_runs,
        }
    finally:
        conn.close()
