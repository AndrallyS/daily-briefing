"""
ai_summarizer.py — GPT-4o-mini powered summarization and translation.
Uses your existing OpenAI API key. Cost: ~$0.02-$0.10/month.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

import config

logger = logging.getLogger(__name__)
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _call(system: str, user: str, max_tokens: int = 120) -> str:
    resp = _get_client().chat.completions.create(
        model=config.OPENAI_MODEL,
        max_tokens=max_tokens,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    # Fix: content can be None — guard against TypeError
    content = resp.choices[0].message.content
    if content is None:
        return ""
    return content.strip()


# ─────────────────────────────────────────────
# Summarize a post
# ─────────────────────────────────────────────

def summarize_post(item: Dict) -> str:
    if not config.OPENAI_SUMMARIZE:
        return ""

    title   = item.get("title", "")
    content = item.get("selftext") or item.get("summary") or ""
    source  = item.get("subreddit") or item.get("source") or ""

    if not content or len(content) < 80:
        return ""

    try:
        result = _call(
            system=(
                "Você é um editor de tecnologia e games. "
                "Resuma o post em exatamente 2 frases em português brasileiro. "
                "Seja direto, informativo e sem repetir o título. "
                "Não use introduções como 'O post fala sobre'."
            ),
            user=f"Fonte: {source}\nTítulo: {title}\nConteúdo: {content[:600]}",
            max_tokens=100,
        )
        logger.debug("Summarized: %s", title[:50])
        return result
    except Exception as exc:
        logger.warning("Summary failed for '%s': %s", title[:40], exc)
        return ""


# ─────────────────────────────────────────────
# Translate a title
# ─────────────────────────────────────────────

def translate_title(title: str, from_lang: str) -> str:
    if not config.OPENAI_TRANSLATE:
        return title

    if from_lang == config.TARGET_LANGUAGE:
        return title

    lang_names = {
        "pt": "português brasileiro", "en": "inglês",
        "ja": "japonês", "es": "espanhol",
        "de": "alemão", "fr": "francês", "ko": "coreano",
    }
    target_name = lang_names.get(config.TARGET_LANGUAGE, "português brasileiro")

    try:
        result = _call(
            system=(
                f"Traduza para {target_name}. "
                "Retorne APENAS o título traduzido, nada mais."
            ),
            user=title,
            max_tokens=80,
        )
        return result if result else title
    except Exception as exc:
        logger.warning("Translation failed: %s", exc)
        return title


# ─────────────────────────────────────────────
# Batch enrich
# ─────────────────────────────────────────────

def enrich_items(items: List[Dict]) -> List[Dict]:
    from langdetect import detect, LangDetectException

    for item in items:
        try:
            lang = detect(item.get("title", ""))
        except LangDetectException:
            lang = "en"
        item["detected_lang"] = lang

        # Translate every non-PT title (simpler than checking SUPPORTED_LANGUAGES)
        if lang != "pt":
            item["title_translated"] = translate_title(item["title"], lang)
        else:
            item["title_translated"] = ""

        item["ai_summary"] = summarize_post(item)

    return items
