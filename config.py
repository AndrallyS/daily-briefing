"""
config.py — Centralized configuration for Daily Briefing Bot v3.
All sensitive values come from environment variables / GitHub Secrets.
Never hardcode credentials here.

Categories:
  gaming   — mainstream gaming news, leaks, releases
  gamedev  — Unity, Blender, Unreal, indie dev, game design
  ai       — AI/ML, LLMs, generative art, AI tools
  tech     — hardware, software, cybersecurity, programming
  br       — Brazilian communities (any topic)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set

try:
    import yaml
    _RAW: Dict = yaml.safe_load(Path("settings.yml").read_text(encoding="utf-8")) or {}
except Exception:
    _RAW = {}

# ── Helpers to read settings.yml ─────────────────────────────
def _setting(section: str, key: str, default):
    return _RAW.get(section, {}).get(key, default) if isinstance(_RAW.get(section), dict) else default

def _disabled_subs() -> Set[str]:
    raw = _RAW.get("subreddits_disabled") or []
    return {str(s).strip().lower() for s in raw if s}

def _disabled_feeds() -> Set[str]:
    raw = _RAW.get("feeds_disabled") or []
    return {str(s).strip() for s in raw if s}

def _extra_subs_from_settings(cat: str) -> List[str]:
    block = (_RAW.get("subreddits_extra") or {}).get(cat) or []
    return [s.strip() for s in block if s]

def _enabled_categories() -> Set[str]:
    cats = (_RAW.get("categories") or {})
    return {k for k, v in cats.items() if v is not False} if cats else {"gaming","gamedev","ai","tech","br"}


# ─────────────────────────────────────────────────────────────
# Reddit — public JSON API (no credentials needed)
# Uses reddit.com/r/{sub}/hot.json — no app registration required
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# OpenAI  →  platform.openai.com/api-keys
# ─────────────────────────────────────────────────────────────
OPENAI_API_KEY:   str  = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL:     str  = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_SUMMARIZE: bool = os.environ.get("OPENAI_SUMMARIZE", "true").lower() == "true"
OPENAI_TRANSLATE: bool = os.environ.get("OPENAI_TRANSLATE", "true").lower() == "true"

# ─────────────────────────────────────────────────────────────
# Notifications — configure at least one channel
# ─────────────────────────────────────────────────────────────

# Telegram (recommended — free, rich formatting)
TELEGRAM_BOT_TOKEN: str  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID:   str  = os.environ.get("TELEGRAM_CHAT_ID", "")
SEND_TELEGRAM:      bool = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# Discord (optional — great for communities)
DISCORD_WEBHOOK_URL: str  = os.environ.get("DISCORD_WEBHOOK_URL", "")
SEND_DISCORD:        bool = bool(DISCORD_WEBHOOK_URL)

# Email / SMTP (optional fallback)
SMTP_HOST:       str  = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT:       int  = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER:       str  = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD:   str  = os.environ.get("SMTP_PASSWORD", "")
EMAIL_RECIPIENT: str  = os.environ.get("EMAIL_RECIPIENT", "")
SEND_EMAIL:      bool = bool(SMTP_USER and SMTP_PASSWORD and EMAIL_RECIPIENT)

# ─────────────────────────────────────────────────────────────
# Fetch tuning — set in settings.yml (preferred) or env vars
# ─────────────────────────────────────────────────────────────
POSTS_PER_SUBREDDIT:  int = int(os.environ.get("POSTS_PER_SUBREDDIT", "15"))

# Alert mode settings
ALERT_MIN_SCORE:      int = int(os.environ.get("ALERT_MIN_SCORE",      "15000"))
ALERT_LOOKBACK_HOURS: int = int(os.environ.get("ALERT_LOOKBACK_HOURS", "12"))

# ─────────────────────────────────────────────────────────────
# Languages
# ─────────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES: List[str] = ["pt", "en", "ja", "es", "de", "fr", "ko"]
# TARGET_LANGUAGE is resolved after settings.yml loads (see bottom of file)


# ─────────────────────────────────────────────────────────────
# Subreddit URL parser
# Accepts: full URL, "r/name", or just "name"
# ─────────────────────────────────────────────────────────────
def _parse_subs(raw: str) -> List[str]:
    results = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        m = re.search(r"(?:reddit\.com/r/|^r/)([A-Za-z0-9_]+)", item)
        if m:
            results.append(m.group(1))
        elif re.match(r"^[A-Za-z0-9_]+$", item):
            results.append(item)
    return results


# ─────────────────────────────────────────────────────────────
# Default subreddits per category
# ─────────────────────────────────────────────────────────────

_GAMING = [
    # Major gaming
    "gaming", "PS5", "XboxSeriesX", "NintendoSwitch", "pcgaming",
    "games", "patientgamers",
    # Specific titles & communities
    "Eldenring", "leagueoflegends", "GlobalOffensive", "VALORANT",
    "Minecraft", "Steam", "SteamDeals",
    # Leaks & news
    "GamingLeaksAndRumours", "GameDeals",
]

_GAMEDEV = [
    # Engines & tools
    "Unity3D", "unrealengine", "godot", "gamemaker",
    # Art & 3D
    "blender", "blenderhelp", "3Dmodeling", "learnblender",
    # Dev community
    "gamedev", "indiegaming", "IndieDev",
    "devblogs", "roguelikedev",
    # Game design
    "gamedesign", "leveldesign",
]

_AI = [
    # Research & models
    "MachineLearning", "artificial", "LocalLLaMA", "ChatGPT",
    "OpenAI", "ClaudeAI", "StableDiffusion",
    # Generative AI & creative
    "MediaSynthesis", "deeplearning",
    # AI in gamedev
    "aivideo", "singularity",
    # Tools
    "AutoGPT",
]

_TECH = [
    # General tech
    "technology", "hardware", "programming", "linux",
    "SoftwareEngineering", "webdev",
    # Security
    "cybersecurity", "netsec", "hacking",
    # Platforms
    "apple", "Android",
    # Science
    "Futurology",
]

_BR = [
    "brasil", "gamesEletronicos", "hardware_br",
    "brdev", "programacao", "investimentos",
    "artificial_br",
]

# Merge defaults + env extras + settings.yml extras, then remove disabled ones
def _build_subs(defaults: List[str], env_key: str, cat: str) -> List[str]:
    """Combine all sources and apply the disabled list from settings.yml."""
    disabled = _disabled_subs()
    combined = (
        defaults
        + _parse_subs(os.environ.get(env_key, ""))
        + _parse_subs(",".join(_extra_subs_from_settings(cat)))
    )
    return [s for s in dict.fromkeys(combined) if s.lower() not in disabled]

GAMING_SUBREDDITS:  List[str] = _build_subs(_GAMING,  "EXTRA_GAMING_SUBREDDITS",  "gaming")
GAMEDEV_SUBREDDITS: List[str] = _build_subs(_GAMEDEV, "EXTRA_GAMEDEV_SUBREDDITS", "gamedev")
AI_SUBREDDITS:      List[str] = _build_subs(_AI,      "EXTRA_AI_SUBREDDITS",      "ai")
TECH_SUBREDDITS:    List[str] = _build_subs(_TECH,    "EXTRA_TECH_SUBREDDITS",    "tech")
BR_SUBREDDITS:      List[str] = _build_subs(_BR,      "EXTRA_BR_SUBREDDITS",      "br")

# Active categories (respects settings.yml categories: true/false)
ENABLED_CATEGORIES: Set[str] = _enabled_categories()

# Fetch tuning — settings.yml values override env vars
MAX_POSTS_IN_REPORT: int = _setting("", "max_posts_per_category",
    int(os.environ.get("MAX_POSTS_IN_REPORT", "10")))
LOOKBACK_HOURS: int = _setting("", "lookback_hours",
    int(os.environ.get("LOOKBACK_HOURS", "36")))
MIN_SCORE: int = _setting("", "min_score",
    int(os.environ.get("MIN_SCORE", "45")))
TARGET_LANGUAGE: str = _setting("", "target_language",
    os.environ.get("TARGET_LANGUAGE", "pt"))

# ─────────────────────────────────────────────────────────────
# RSS feeds per category
# ─────────────────────────────────────────────────────────────

GAMING_RSS_FEEDS: List[str] = [
    "https://kotaku.com/rss",
    "https://www.gamespot.com/feeds/mashup/",
    "https://feeds.arstechnica.com/arstechnica/gaming",
    "https://www.eurogamer.net/?format=rss",
    "https://rockpapershotgun.com/feed",
]

GAMEDEV_RSS_FEEDS: List[str] = [
    "https://www.gamedeveloper.com/rss.xml",
    "https://unity.com/blog/rss.xml",
    "https://blogs.unity.com/feed",
    "https://www.unrealengine.com/en-US/rss",
    "https://80.lv/feed/",                          # 3D/game art news
    "https://www.blendernation.com/feed/",
]

AI_RSS_FEEDS: List[str] = [
    "https://openai.com/blog/rss/",
    "https://www.anthropic.com/news/rss",
    "https://huggingface.co/blog/feed.xml",
    "https://deepmind.google/blog/rss/",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
]

TECH_RSS_FEEDS: List[str] = [
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://threatpost.com/feed/",
    "https://techcrunch.com/feed/",
]

# Apply feeds_disabled from settings.yml
def _filter_feeds(feeds: List[str]) -> List[str]:
    disabled = _disabled_feeds()
    return [f for f in feeds if f not in disabled]

GAMING_RSS_FEEDS  = _filter_feeds(GAMING_RSS_FEEDS)
GAMEDEV_RSS_FEEDS = _filter_feeds(GAMEDEV_RSS_FEEDS)
AI_RSS_FEEDS      = _filter_feeds(AI_RSS_FEEDS)
TECH_RSS_FEEDS    = _filter_feeds(TECH_RSS_FEEDS)

# ─────────────────────────────────────────────────────────────
# Keyword signals (boost relevance score)
# ─────────────────────────────────────────────────────────────
HIGH_SIGNAL_KEYWORDS: List[str] = [
    # Gaming
    "leak", "leaked", "exclusive", "breaking", "announced", "confirmed",
    "release date", "trailer", "gameplay", "rumor", "official",
    "early access", "launch", "update", "DLC", "sequel", "datamine", "datamined", "insider info", "dev update",
    "roadmap", "season update", "hotfix", "live now",
    "shadow drop", "preload", "review embargo",
    "first look", "hands-on", "closed beta", "alpha test",
    # Gamedev / Tools
    "tutorial", "open source", "free asset", "plugin", "workflow",
    "new version", "major update", "blender", "unity", "unreal", "asset pack", "devlog", "production ready", "pipeline",
    "optimization", "performance boost", "shader",
    "procedural", "addon", "toolkit",
    "engine update", "render update", "workflow improvement",
    "integration", "cross-platform",
    # AI
    "AI", "GPT", "model", "benchmark", "fine-tuned", "open source model",
    "new release", "beats", "surpasses", "state of the art", "multimodal", "inference", "token limit",
    "context window", "fine tuning", "quantization",
    "distillation", "agent", "autonomous",
    "open weights", "alignment", "hallucination fix",
    "training data", "benchmark score", "real world test", "Claude",
    # Tech / Security
    "vulnerability", "exploit", "breach", "zero-day", "patch",
    "acquisition", "layoffs", "lawsuit", "ban",
    "record", "first ever",
]

CRITICAL_ALERT_KEYWORDS: List[str] = [
    "zero-day", "critical vulnerability", "data breach",
    "actively exploited", "emergency patch", "RCE",
    "acquired by", "acquisition confirmed",
    "release date confirmed", "official announcement",
    "direct sequel confirmed", "shutdown",
]

# ─────────────────────────────────────────────────────────────
# Category display metadata (used in HTML + Telegram)
# ─────────────────────────────────────────────────────────────
CATEGORY_META = {
    "gaming":  {"label": "Gaming",           "emoji": "🎮", "color": "#e2571e"},
    "gamedev": {"label": "Game Dev & Tools", "emoji": "🛠️",  "color": "#7c3aed"},
    "ai":      {"label": "Inteligência Artificial", "emoji": "🤖", "color": "#0891b2"},
    "tech":    {"label": "Tech & Segurança", "emoji": "⚡", "color": "#0f766e"},
    "br":      {"label": "Brasil",           "emoji": "🇧🇷", "color": "#16a34a"},
}
