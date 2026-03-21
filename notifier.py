"""
notifier.py — Multi-channel notification delivery.
Supports Telegram Bot API, Discord Webhooks, and SMTP (fallback).
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

import config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Telegram
# ─────────────────────────────────────────────

def _escape_html(text: str) -> str:
    """Escape text for use inside HTML tag content."""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;"))

def _escape_url(url: str) -> str:
    """Escape URL for use inside href='...' attributes (single-quoted)."""
    return (url
        .replace("&", "&amp;")
        .replace("'", "%27")
        .replace('"', "%22")
        .replace("<", "%3C")
        .replace(">", "%3E"))


def _build_telegram_message(briefing: Dict[str, List[Dict]], mode: str = "daily") -> str:
    now  = datetime.now(tz=timezone.utc)
    date = now.strftime("%d/%m/%Y %H:%M UTC")

    if mode == "alert":
        lines = [f"\U0001f6a8 <b>ALERTA \u2014 {date}</b>\n"]
    else:
        lines = [f"\U0001f5de\ufe0f <b>Daily Briefing \u2014 {date}</b>\n"]

    section_icons = {
        "gaming":  "\U0001f3ae",
        "gamedev": "\U0001f6e0",
        "ai":      "\U0001f916",
        "tech":    "\u26a1",
        "br":      "\U0001f1e7\U0001f1f7",
    }

    for cat, items in briefing.items():
        if not items:
            continue
        meta  = config.CATEGORY_META.get(cat, {})
        label = meta.get("label", cat.upper())
        icon  = section_icons.get(cat, "\U0001f4cc")
        lines.append(f"\n{icon} <b>{label}</b>")

        for i, item in enumerate(items, 1):
            display_title = _escape_html(item.get("title_translated") or item.get("title", ""))
            orig_title    = _escape_html(item.get("title", ""))
            translated    = bool(item.get("title_translated"))
            ext_url       = item.get("url", "")
            permalink     = item.get("permalink", "")
            is_reddit     = item.get("source") == "reddit"
            score         = item.get("score", 0)
            comments      = item.get("num_comments", 0)
            sub           = item.get("subreddit", "")
            sentiment     = item.get("sentiment", "neutral")
            ai_sum        = _escape_html(item.get("ai_summary", ""))
            sent_icon     = {"positive": "\U0001f7e2", "negative": "\U0001f534", "neutral": "\u26aa"}.get(sentiment, "\u26aa")

            link_url = _escape_url(ext_url if ext_url else permalink)
            line = f"\n<b>{i}.</b> {sent_icon} <a href='{link_url}'>{display_title}</a>"

            if translated:
                line += f"\n   <i>({orig_title[:80]})</i>"

            if is_reddit and sub:
                line += f"\n   \u2514 r/{sub}"
                if score:
                    line += f" \u00b7 \u25b2{score:,} \u00b7 \U0001f4ac{comments:,}"
                if permalink and permalink != ext_url:
                    safe_permalink = _escape_url(permalink)
                    line += f" \u00b7 <a href='{safe_permalink}'>ver discuss\u00e3o</a>"
            elif not is_reddit:
                source = _escape_html(item.get("source", "RSS")[:30])
                line += f"\n   \u2514 {source}"

            if ai_sum:
                line += f"\n   <i>{ai_sum}</i>"

            lines.append(line)

    lines.append("\n\n<a href='https://github.com/AndrallyS/daily-briefing'>\U0001f4c4 Ver briefing completo</a>")
    return "\n".join(lines)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
def send_telegram(briefing: Dict[str, List[Dict]], mode: str = "daily") -> bool:
    if not config.SEND_TELEGRAM:
        logger.info("Telegram disabled (no token/chat_id)")
        return False

    text = _build_telegram_message(briefing, mode)

    # Telegram has a 4096 char limit per message — split if needed
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]

    for chunk in chunks:
        resp = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id":    config.TELEGRAM_CHAT_ID,
                "text":       chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        if not resp.ok:
            logger.error("Telegram error: %s — %s", resp.status_code, resp.text[:200])
            return False

    logger.info("✅ Telegram message sent (%d chars)", len(text))
    return True


# ─────────────────────────────────────────────
# Discord
# ─────────────────────────────────────────────

def _build_discord_embeds(briefing: Dict[str, List[Dict]], mode: str = "daily") -> List[Dict]:
    now    = datetime.now(tz=timezone.utc)
    colors = {"gaming": 0xE2571E, "tech": 0x0F766E, "br": 0x22C55E}

    embeds = []
    for cat, items in briefing.items():
        if not items:
            continue

        fields = []
        for i, item in enumerate(items, 1):
            title    = (item.get("title_translated") or item.get("title", ""))[:200]
            url      = item.get("url") or item.get("permalink", "")
            score    = item.get("score", 0)
            comments = item.get("num_comments", 0)
            ai_sum   = item.get("ai_summary", "")

            value = f"[{title}]({url})"
            if score:
                value += f"\n▲{score:,} · 💬{comments:,}"
            if ai_sum:
                value += f"\n*{ai_sum[:100]}*"

            fields.append({
                "name":   f"#{i}",
                "value":  value[:1024],
                "inline": False,
            })

        section_titles = {
            "gaming": "🎮 Gaming Highlights",
            "tech":   "⚡ Technology & Security",
            "br":     "🇧🇷 Brasil",
        }
        embeds.append({
            "title":     section_titles.get(cat, cat.upper()),
            "color":     colors.get(cat, 0x334155),
            "fields":    fields[:10],
            "footer":    {"text": f"DailyBriefingBot · {now.strftime('%d/%m/%Y %H:%M UTC')}"},
            "timestamp": now.isoformat(),
        })

    return embeds


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
def send_discord(briefing: Dict[str, List[Dict]], mode: str = "daily") -> bool:
    if not config.SEND_DISCORD:
        logger.info("Discord disabled (no webhook URL)")
        return False

    embeds = _build_discord_embeds(briefing, mode)

    title   = "🚨 ALERTA DE BREAKING NEWS" if mode == "alert" else "🗞️ Daily Briefing"
    content = f"**{title}** — {datetime.now(tz=timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}"

    # Discord allows max 10 embeds per message — split if needed
    for i in range(0, len(embeds), 10):
        resp = requests.post(
            config.DISCORD_WEBHOOK_URL,
            json={
                "content": content if i == 0 else "",
                "embeds":  embeds[i:i+10],
            },
            timeout=15,
        )
        if resp.status_code not in (200, 204):
            logger.error("Discord error: %s — %s", resp.status_code, resp.text[:200])
            return False

    logger.info("✅ Discord message sent (%d embeds)", len(embeds))
    return True


# ─────────────────────────────────────────────
# E-mail (kept as fallback)
# ─────────────────────────────────────────────

def send_email(html_body: str, plain_body: str, subject: Optional[str] = None) -> bool:
    if not config.SEND_EMAIL:
        logger.info("Email disabled (missing SMTP credentials)")
        return False

    now = datetime.now(tz=timezone.utc)
    subj = subject or f"🗞️ Daily Briefing — {now.strftime('%d/%m/%Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subj
    msg["From"]    = config.SMTP_USER
    msg["To"]      = config.EMAIL_RECIPIENT
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,  "html",  "utf-8"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as srv:
            srv.ehlo(); srv.starttls(context=context); srv.ehlo()
            srv.login(config.SMTP_USER, config.SMTP_PASSWORD)
            srv.sendmail(config.SMTP_USER, [config.EMAIL_RECIPIENT], msg.as_bytes())
        logger.info("✅ Email sent to %s", config.EMAIL_RECIPIENT)
        return True
    except Exception as exc:
        logger.error("❌ Email failed: %s", exc)
        return False


# ─────────────────────────────────────────────
# Unified dispatch
# ─────────────────────────────────────────────

def dispatch(
    briefing: Dict[str, List[Dict]],
    html_body: str = "",
    plain_body: str = "",
    mode: str = "daily",
) -> Dict[str, bool]:
    """Send to all configured channels. Returns status per channel."""
    results = {}

    if config.SEND_TELEGRAM:
        results["telegram"] = send_telegram(briefing, mode)

    if config.SEND_DISCORD:
        results["discord"] = send_discord(briefing, mode)

    if config.SEND_EMAIL and html_body:
        subject = "🚨 ALERTA Breaking News" if mode == "alert" else None
        results["email"] = send_email(html_body, plain_body, subject)

    if not results:
        logger.warning("No notification channels configured.")

    return results
