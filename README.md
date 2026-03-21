# 🗞️ Daily Briefing Bot

<div align="center">

[![GitHub Actions](https://img.shields.io/badge/Powered%20by-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![OpenAI](https://img.shields.io/badge/AI-GPT--4o--mini-412991?logo=openai&logoColor=white)](https://openai.com)
[![No Reddit App](https://img.shields.io/badge/Reddit-No%20App%20Needed-FF4500?logo=reddit&logoColor=white)](README.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Cost](https://img.shields.io/badge/Monthly%20Cost-~%240.02-brightgreen)](README.md#cost)

**An automated daily intelligence briefing covering Games, Game Dev, AI, Blender, and Tech.**

Pulls from 60+ subreddits and RSS feeds → ranks by relevance → summarizes with AI →
delivers to Telegram, Discord, or Email. Runs 100% free on GitHub Actions.

**No Reddit account or app registration required.**

[Features](#features) · [Quick Start](#quick-start) · [Configuration](#configuration) · [Adding Subreddits](#adding-your-own-subreddits) · [Contributing](#contributing)

</div>

---

## Features

| Feature | Description |
|---|---|
| 📡 **60+ Sources** | Gaming, Game Dev, Unity, Blender, AI/ML, Tech, Security, Brasil |
| 🔓 **No Reddit App** | Uses Reddit's public JSON API — no registration needed |
| 🤖 **AI Summaries** | GPT-4o-mini summarizes long posts in 2 sentences (PT-BR) |
| 🏆 **Smart Ranking** | Multi-factor relevance score: upvotes + comments + keywords + recency |
| 😊 **Sentiment** | VADER analysis shows positive/negative/neutral per post |
| 🚨 **Daily Alerts** | Second scan at noon catches breaking news (score ≥ 15k + keywords) |
| 🌍 **Multilingual** | Auto-detects and translates non-PT-BR titles |
| 📦 **Dedup Cache** | JSON cache prevents the same post from appearing twice |
| 📊 **History** | SQLite tracks 30-day trends (top subreddits, keywords) |
| 🌐 **Telegram** | Rich HTML messages with AI summaries directly in your phone |
| 🎮 **Discord** | Embeds with color-coded sections per category |
| 📧 **Email** | Full HTML briefing as fallback |
| 🌐 **Static Site** | GitHub Pages publishes briefing as a website (free) |

---

## How it works — Reddit access

This bot uses Reddit's **public JSON API** — the same data your browser loads when you open any subreddit. No account, no app registration, no API keys for Reddit. Just add `.json` to any Reddit URL and you get structured data.

```
https://www.reddit.com/r/gaming/hot.json
```

This works for any **public** subreddit. Private or NSFW-gated subreddits are skipped automatically.

---

## Quick Start

### Prerequisites
- GitHub account (free)
- OpenAI account with API key
- Telegram account (recommended, free)

> **That's it.** No Reddit account needed. No Reddit app. No API keys for Reddit.

### 1. Fork or clone this repository

```bash
git clone https://github.com/AndrallyS/daily-briefing.git
cd daily-briefing
```

### 2. Create a Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → choose a name → copy the **Bot Token**
3. Search **@userinfobot** → send any message → copy your **Chat ID** (the number)
4. Open your bot → click **Start**

### 3. Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

**Only 3 required secrets:**

| Secret | Where to find it |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHAT_ID` | From @userinfobot |

**Optional secrets:**

| Secret | Purpose |
|---|---|
| `DISCORD_WEBHOOK_URL` | Discord notifications |
| `SMTP_USER` + `SMTP_PASSWORD` + `EMAIL_RECIPIENT` | Email delivery |
| `EXTRA_GAMING_SUBREDDITS` | Your extra gaming subs |
| `EXTRA_GAMEDEV_SUBREDDITS` | Your extra gamedev subs |
| `EXTRA_AI_SUBREDDITS` | Your extra AI subs |
| `EXTRA_BR_SUBREDDITS` | Your extra Brazilian subs |

### 4. Test the workflow

1. Go to **Actions** tab → **Daily Briefing** → **Run workflow** → **Run workflow**
2. Watch the logs in real time (~2 minutes)
3. Check your Telegram for the first briefing!

---

## Adding Your Own Subreddits

No code changes needed. Create a GitHub Secret with any format:

```
# EXTRA_GAMING_SUBREDDITS — accepts any of these formats:
https://www.reddit.com/r/Eldenring, VALORANT, r/Minecraft, SteamDeals
```

The bot auto-parses URLs, `r/name`, or plain names. ✓

---

## Personalizing with settings.yml

Edit `settings.yml` in the repo root to customize without touching any Python:

```yaml
# Disable entire categories
categories:
  gaming:  true
  gamedev: true
  ai:      true
  tech:    true
  br:      false    # disable Brazilian section

# Remove specific subreddits
subreddits_disabled:
  - blender
  - blenderhelp

# Remove specific RSS feeds
feeds_disabled:
  - https://www.blendernation.com/feed/

# Tune the output
max_posts_per_category: 5
lookback_hours: 24
min_score: 50
target_language: "pt"
```

---

## Configuration

### Schedule

| Workflow | UTC | BRT | Action |
|---|---|---|---|
| Daily Briefing | 07:00 | 04:00 | Full briefing — all categories |
| Alert Scan | 14:00 | 11:00 | Breaking news only (silent if none) |

### Alert Thresholds

In `.github/workflows/daily_alert.yml`:
```yaml
ALERT_MIN_SCORE:      "15000"   # minimum upvotes to trigger
ALERT_LOOKBACK_HOURS: "12"      # scan last N hours
```

---

## Project Structure

```
daily-briefing/
├── main.py              # Orchestrator — daily or alert mode
├── config.py            # All settings via environment variables
├── settings.yml         # User personalization (no Python needed)
├── reddit_fetcher.py    # Public Reddit JSON API collector
├── rss_fetcher.py       # RSS/Atom feed collector
├── ranker.py            # Relevance scoring + VADER sentiment
├── ai_summarizer.py     # OpenAI summaries + translation
├── html_renderer.py     # Static HTML + plain text renderer
├── notifier.py          # Telegram + Discord + Email delivery
├── storage.py           # SQLite history and trend stats
├── cache.py             # seen_ids.json deduplication cache
├── requirements.txt     # Python dependencies
├── seen_ids.json        # Auto-generated: tracks sent post IDs
├── docs/
│   └── index.html       # Auto-generated: latest briefing (GitHub Pages)
└── .github/
    └── workflows/
        ├── daily_briefing.yml
        └── daily_alert.yml
```

---

## Relevance Scoring

Each post/article receives a score from 0–100:

| Component | Max | Formula |
|---|---|---|
| Upvotes | 35 | `log10(score + 1) × 10` |
| Comments | 15 | `log10(comments + 1) × 5` |
| Upvote ratio | 10 | ≥95% → 10, ≥85% → 7, ≥70% → 4 |
| Signal keywords | 25 | +6 per match (max 4) |
| Recency | 15 | <2h → 15, <6h → 12, <24h → 4 |

---

## Cost

| Service | Cost/month |
|---|---|
| GitHub Actions | **$0.00** (unlimited on public repos) |
| GitHub Pages | **$0.00** |
| Reddit API | **$0.00** (public JSON, no account needed) |
| Telegram / Discord | **$0.00** |
| OpenAI API (GPT-4o-mini, ~10 posts/day) | **~$0.02** |
| **Total** | **~$0.02/month** |

---

## GitHub Pages

Enable the free briefing website:

1. Repo → **Settings → Pages**
2. Source: **Deploy from a branch** → Branch: `main` → Folder: `/docs`
3. Save → live at `https://YOUR_USERNAME.github.io/daily-briefing/`

---

## Running Locally

```bash
git clone https://github.com/YOUR_USERNAME/daily-briefing.git
cd daily-briefing
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export OPENAI_API_KEY="sk-..."
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

python main.py daily    # full briefing
python main.py alert    # alert scan only
```

---

## Contributing

1. Fork → create branch → make changes → test locally → open PR
2. See [CONTRIBUTING.md](CONTRIBUTING.md) for details

**Easy contributions:** add RSS feeds, add subreddits, improve scoring, add notification channels.

---

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

## Dependencies

```
requests        — HTTP requests (Reddit public API + notifications)
feedparser      — RSS/Atom feed parser
openai          — GPT-4o-mini for summaries and translations
langdetect      — Language detection
vaderSentiment  — Sentiment analysis
tenacity        — Automatic retry on network failures
PyYAML          — settings.yml parsing
```
