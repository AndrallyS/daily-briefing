# Contributing to Daily Briefing Bot

Thank you for your interest in contributing! This project welcomes improvements of all sizes.

## How to contribute

### 1. Report a bug or suggest a feature
Open an [Issue](../../issues) describing:
- What happened (or what you'd like to see)
- Steps to reproduce (for bugs)
- Your environment (Python version, OS)

### 2. Submit a Pull Request

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/daily-briefing.git
cd daily-briefing

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Test locally (see README → Running Locally)
python main.py daily

# Commit and push
git commit -m "feat: describe your change clearly"
git push origin feature/your-feature-name

# Open a PR on GitHub
```

## Easy contributions (good first issues)

| Task | File | Difficulty |
|---|---|---|
| Add a new RSS feed | `config.py` | ⭐ Easy |
| Add subreddits to a category | `config.py` | ⭐ Easy |
| Add a new keyword to signal list | `config.py` | ⭐ Easy |
| Improve the HTML email template | `html_renderer.py` | ⭐⭐ Medium |
| Add a new notification channel (WhatsApp, Slack…) | `notifier.py` | ⭐⭐ Medium |
| Add a new category (e.g. "music", "sports") | `config.py` + `main.py` | ⭐⭐ Medium |
| Improve the relevance scoring formula | `ranker.py` | ⭐⭐⭐ Advanced |

## Code style

- Python 3.11+
- Type hints on all function signatures
- Docstrings on all modules
- Max line length: 100 characters
- Use `logging` (not `print`) for output

## Questions?

Open an Issue and tag it with `question`. We're happy to help!
