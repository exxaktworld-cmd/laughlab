# LaughLab AI — Comedy Writing Engine

A free-first, Gemini-powered research and comedy-writing project for original 40–45 second commentary scripts about viral internet culture, celebrity news, influencer behaviour, bizarre online stories and public absurdity.

**Creative north star:** “This guy just said what I was thinking, but in a way I never could.”

## What this starter does

1. Reads public RSS feeds from selected Reddit communities and Google News searches.
2. Filters stale/duplicate stories and ranks candidates using freshness and engagement signals where available.
3. Uses Gemini in separate stages: premise generation, script drafting, editorial critique and punch-up.
4. Enforces a short-form word-count target and basic quality gates.
5. Saves three selected scripts plus research notes in `output/`.
6. Runs daily through GitHub Actions. It does **not** publish to social media.

This is a first working foundation, not a claim that AI can objectively guarantee laughter. Real audience feedback must guide improvement.

## Create your repository

Choose any repository name in GitHub. Suggested name: `laughlab-ai` (you chose a custom name, so this is only a suggestion).

On Android:
1. Open GitHub in Chrome and sign in.
2. Tap **+** → **New repository**.
3. Enter your chosen repository name.
4. Choose **Public** or **Private**; either works.
5. Select **Add a README** only if you are creating an empty repository? **Do not add a README** when uploading this starter, to avoid a merge/conflict.
6. Create the repository.
7. Extract this ZIP on your phone. Upload the extracted files and folders to the repository using GitHub's web upload interface. If the mobile interface does not show folder upload, use GitHub's browser desktop-site mode.

## Configure Gemini

1. Open [Google AI Studio](https://aistudio.google.com/).
2. Create an API key.
3. In your GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**.
4. Name it `GEMINI_API_KEY` and paste the key.
5. Optionally add a repository variable `GEMINI_MODEL`. The default is `gemini-2.5-flash`; change it to a model currently available to your account if needed.

Never put the API key in a source file, README, issue, or commit.

## Run locally

Python 3.11+ recommended.

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
python main.py
```

On Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your-key"
python main.py
```

## Daily automation

The workflow runs at 12:30 UTC (18:00 India time) and can also be started manually from **Actions → Daily LaughLab Scripts → Run workflow**.

It commits generated files under `output/`. It never posts to YouTube, Instagram, Facebook or any other platform.

## Current research sources

- Reddit RSS feeds configured in `config/sources.yaml`.
- Google News RSS searches focused on viral internet culture and celebrity stories.

RSS availability, community rules, rate limits and content quality can change. The system stores source links and excerpts; it does not bypass logins, private communities or access controls. Reddit post scores/comments are not guaranteed to appear in RSS.

## Editorial standards

- Roast public behaviour, public decisions, hypocrisy, public personas and public claims.
- Do not invent allegations or present speculation as fact.
- Do not target private individuals or protected traits.
- Clearly separate verified facts from comic exaggeration.
- Do not copy comedians' jokes, scripts, catchphrases or distinctive phrasing.
- The system can reject a story or draft rather than force a weak script.

## Output format

Each run creates:
- `output/YYYY-MM-DD/scripts.md`
- `output/YYYY-MM-DD/research.json`

## Project map

```text
.github/workflows/daily-comedy.yml
config/settings.yaml
config/sources.yaml
docs/comedy-science.md
docs/voice-bible.md
prompts/*.md
src/config.py
src/feeds.py
src/gemini.py
src/pipeline.py
src/quality.py
tests/test_quality.py
main.py
```

## Important free-tier note

Google AI Studio free-tier availability, model access, quotas, and data-use terms can change. Check Google's current documentation before relying on a model or processing sensitive information. This project is designed to be configurable, not tied permanently to one model.
