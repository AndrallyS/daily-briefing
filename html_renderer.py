"""
html_renderer.py v3 — Professional HTML briefing.
Five categories: Gaming · Game Dev & Tools · AI · Tech & Security · Brasil
Includes AI summaries, sentiment indicators, translated titles, and 30-day stats.
"""

from __future__ import annotations

import html as hl
from datetime import datetime, timezone
from typing import Dict, List

import config
import storage


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _badge(text: str, color: str, bg: str = "") -> str:
    if not bg:
        bg = color
    return (
        f'<span style="display:inline-block;background:{bg};color:#fff;'
        f'font-size:10px;font-weight:700;letter-spacing:.05em;'
        f'text-transform:uppercase;padding:2px 8px;border-radius:4px;'
        f'margin-right:3px;">{hl.escape(text)}</span>'
    )

def _sent_icon(s: str) -> str:
    return {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(s, "⚪")

def _kw_pills(kws: List[str]) -> str:
    if not kws:
        return ""
    pills = "".join(
        f'<span style="display:inline-block;background:#fef9c3;color:#713f12;'
        f'font-size:10px;font-weight:600;padding:1px 5px;border-radius:3px;'
        f'margin:1px 2px;">{hl.escape(k)}</span>'
        for k in kws[:4]
    )
    return f'<div style="margin-top:5px;line-height:2;">{pills}</div>'


# ─────────────────────────────────────────────────────────────
# Card
# ─────────────────────────────────────────────────────────────

def _render_card(item: Dict, rank: int, accent: str) -> str:
    display_title = hl.escape(item.get("title_translated") or item.get("title", ""))
    orig_title    = hl.escape(item.get("title", ""))
    translated    = bool(item.get("title_translated"))
    url           = hl.escape(item.get("url") or item.get("permalink", "#"))
    permalink     = hl.escape(item.get("permalink", url))
    ai_sum        = hl.escape(item.get("ai_summary", ""))
    flair         = item.get("flair", "")
    sentiment     = item.get("sentiment", "neutral")
    score         = item.get("score", 0)
    comments      = item.get("num_comments", 0)
    ratio         = item.get("upvote_ratio", 0)
    relevance     = item.get("relevance_score", 0)
    sub           = item.get("subreddit", "")
    source        = item.get("source", "")
    created       = item.get("created_at")
    time_str      = created.strftime("%d/%m %H:%M") if created else ""
    is_reddit     = source == "reddit"

    rank_colors = {1: "#f59e0b", 2: "#94a3b8", 3: "#cd7c3a"}
    rank_color  = rank_colors.get(rank, "#334155")

    stat_parts = []
    if score:   stat_parts.append(f"▲ {score:,}")
    if comments:stat_parts.append(f"💬 {comments:,}")
    if ratio:   stat_parts.append(f"👍 {int(ratio*100)}%")
    stat_parts.append(f"⭐ {relevance:.1f}")

    source_badge = (
        _badge(f"r/{sub}", "#e2571e") if is_reddit
        else _badge(source[:28], "#0f766e")
    )
    flair_badge = _badge(flair, "#6366f1") if flair and flair != "article" else ""
    orig_note   = (
        f'<div style="font-size:11px;color:#94a3b8;margin-top:2px;font-style:italic;">'
        f'Original: {orig_title[:90]}{"…" if len(orig_title)>90 else ""}</div>'
    ) if translated else ""
    ai_block = (
        f'<p style="font-size:13px;color:#334155;margin:8px 0 0;line-height:1.6;'
        f'border-left:3px solid {accent}30;padding-left:9px;font-style:italic;">'
        f'{ai_sum}</p>'
    ) if ai_sum else ""
    read_link = "→ Abrir no Reddit" if is_reddit else "→ Ler artigo completo"

    return f"""
<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
  padding:16px 20px;margin-bottom:12px;position:relative;
  box-shadow:0 1px 3px rgba(0,0,0,.05);">
  <div style="position:absolute;top:-9px;left:16px;background:{rank_color};
    color:#fff;font-weight:800;font-size:11px;width:22px;height:22px;
    border-radius:50%;display:flex;align-items:center;justify-content:center;">
    #{rank}</div>
  <div style="display:flex;align-items:center;flex-wrap:wrap;gap:3px;
    margin-top:4px;margin-bottom:8px;">
    {source_badge}{flair_badge}
    <span style="margin-left:auto;font-size:11px;color:#94a3b8;">
      {_sent_icon(sentiment)} {time_str}
    </span>
  </div>
  <a href="{url}" target="_blank"
    style="color:#0f172a;font-weight:700;font-size:14px;line-height:1.4;
    text-decoration:none;display:block;font-family:'Georgia',serif;">
    {display_title}
  </a>
  {orig_note}
  {ai_block}
  <div style="font-size:11px;color:#64748b;margin-top:6px;
    font-family:'Courier New',monospace;">
    {"  ·  ".join(stat_parts)}
  </div>
  {_kw_pills(item.get("matched_keywords", []))}
  <div style="margin-top:9px;">
    <a href="{permalink}" target="_blank"
      style="font-size:12px;color:#3b82f6;font-weight:600;text-decoration:none;">
      {read_link}
    </a>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────
# Section
# ─────────────────────────────────────────────────────────────

def _render_section(cat: str, items: List[Dict]) -> str:
    if not items:
        return ""
    meta   = config.CATEGORY_META[cat]
    label  = meta["label"]
    emoji  = meta["emoji"]
    accent = meta["color"]
    cards  = "".join(_render_card(item, i + 1, accent) for i, item in enumerate(items))
    return f"""
<div style="margin-bottom:36px;">
  <div style="display:flex;align-items:center;margin-bottom:16px;
    padding-bottom:10px;border-bottom:3px solid {accent};">
    <span style="font-size:22px;margin-right:10px;">{emoji}</span>
    <h2 style="margin:0;font-size:19px;font-weight:800;color:#0f172a;
      font-family:'Georgia',serif;letter-spacing:-.01em;">{label}</h2>
    <span style="margin-left:auto;background:{accent};color:#fff;
      font-size:11px;font-weight:700;padding:2px 9px;border-radius:20px;">
      {len(items)} destaques
    </span>
  </div>
  {cards}
</div>"""


# ─────────────────────────────────────────────────────────────
# Stats section (from SQLite)
# ─────────────────────────────────────────────────────────────

def _render_stats() -> str:
    stats = storage.get_stats(days=30)
    if not stats or not stats.get("total_runs", 0):
        return ""

    total_runs = stats["total_runs"]
    top_subs   = stats.get("top_subreddits", [])[:6]
    top_kws    = stats.get("top_keywords", [])[:10]

    subs_html = "".join(
        f'<div style="display:flex;justify-content:space-between;font-size:12px;'
        f'padding:4px 0;border-bottom:.5px solid #e2e8f0;">'
        f'<span style="color:#334155;">r/{hl.escape(sub)}</span>'
        f'<span style="color:#94a3b8;font-family:monospace;">{count}×</span></div>'
        for sub, count in top_subs
    )
    kws_html = "".join(
        f'<span style="display:inline-block;background:#f1f5f9;color:#334155;'
        f'font-size:11px;padding:2px 7px;border-radius:4px;margin:2px;">'
        f'{hl.escape(kw)} <span style="color:#94a3b8;">×{n}</span></span>'
        for kw, n in top_kws
    )

    return f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
  padding:18px 20px;margin-bottom:32px;">
  <div style="font-size:13px;font-weight:700;color:#0f172a;
    font-family:'Georgia',serif;margin-bottom:14px;">
    📈 Últimos {total_runs} dias — tendências
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
    <div>
      <div style="font-size:10px;font-weight:700;color:#94a3b8;
        text-transform:uppercase;letter-spacing:.07em;margin-bottom:8px;">
        Top subreddits
      </div>
      {subs_html}
    </div>
    <div>
      <div style="font-size:10px;font-weight:700;color:#94a3b8;
        text-transform:uppercase;letter-spacing:.07em;margin-bottom:8px;">
        Keywords em alta
      </div>
      {kws_html}
    </div>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────
# Full HTML page
# ─────────────────────────────────────────────────────────────

def render_html(briefing: Dict[str, List[Dict]]) -> str:
    now      = datetime.now(tz=timezone.utc)
    date_str = now.strftime("%d de %B de %Y")
    time_str = now.strftime("%H:%M UTC")
    total    = sum(len(v) for v in briefing.values())

    category_order = ["gaming", "gamedev", "ai", "tech", "br"]
    sections = "".join(
        _render_section(cat, briefing.get(cat, []))
        for cat in category_order
    )

    header_pills = "".join(
        f'<span style="background:{m["color"]}22;color:{m["color"]};'
        f'font-size:11px;font-weight:700;padding:3px 10px;border-radius:12px;'
        f'border:1px solid {m["color"]}44;">{m["emoji"]} {m["label"]}</span>'
        for m in config.CATEGORY_META.values()
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Daily Briefing — {date_str}</title>
  <meta name="description" content="Automated daily briefing: Games, Game Dev, AI, Tech and more."/>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#334155;line-height:1.6;}}
    @media(max-width:600px){{.wrap{{padding:16px!important;}}}}
  </style>
</head>
<body>

<!-- HEADER -->
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 55%,#0f172a 100%);padding:0 20px;">
  <div style="max-width:700px;margin:0 auto;padding:40px 20px;text-align:center;">
    <div style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;
      color:#475569;font-weight:600;margin-bottom:10px;">
      Daily Briefing · Auto-generated
    </div>
    <h1 style="font-size:30px;font-weight:900;color:#f8fafc;
      font-family:'Georgia',serif;letter-spacing:-.02em;margin-bottom:8px;">
      🗞️ Games · Dev · AI · Tech
    </h1>
    <p style="color:#94a3b8;font-size:13px;margin-bottom:18px;">
      {date_str} · {time_str} · {total} destaques
    </p>
    <div style="display:flex;justify-content:center;flex-wrap:wrap;gap:6px;">
      {header_pills}
    </div>
  </div>
</div>

<!-- BODY -->
<div class="wrap" style="max-width:700px;margin:0 auto;padding:28px 20px;">
  {_render_stats()}
  {sections}

  <!-- FOOTER -->
  <div style="text-align:center;padding:20px 0 4px;border-top:1px solid #e2e8f0;margin-top:8px;">
    <p style="font-size:11px;color:#94a3b8;line-height:2;">
      Gerado por <strong>Daily Briefing Bot v3</strong> · 
      <a href="https://github.com/YOUR_USERNAME/daily-briefing"
        style="color:#94a3b8;">GitHub</a><br/>
      Reddit API · RSS · GPT-4o-mini · VADER Sentiment · GitHub Actions
    </p>
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Plain text
# ─────────────────────────────────────────────────────────────

def render_plaintext(briefing: Dict[str, List[Dict]]) -> str:
    now   = datetime.now(tz=timezone.utc)
    lines = [
        f"DAILY BRIEFING v3 — {now.strftime('%d/%m/%Y %H:%M UTC')}",
        "=" * 64, "",
    ]
    for cat, meta in config.CATEGORY_META.items():
        items = briefing.get(cat, [])
        if not items:
            continue
        lines += [f"{meta['emoji']}  {meta['label'].upper()}", "-" * 64]
        for i, item in enumerate(items, 1):
            title = item.get("title_translated") or item.get("title", "")
            lines.append(f"#{i}  {title}")
            if item.get("source") == "reddit":
                lines.append(f"    r/{item.get('subreddit')} · ▲{item.get('score',0):,}")
            if item.get("ai_summary"):
                lines.append(f"    → {item['ai_summary']}")
            lines.append(f"    {item.get('url') or item.get('permalink','')}")
            lines.append("")
        lines.append("")
    lines += ["─" * 64, "Daily Briefing Bot v3 · github.com/YOUR_USERNAME/daily-briefing"]
    return "\n".join(lines)
