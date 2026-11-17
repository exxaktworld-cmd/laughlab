from datetime import datetime, timezone
from .config import load_config
from .feeds import collect_stories
from .gemini import GeminiClient
from .quality import acceptable_candidate, validate_script


def _read_prompt(root, name):
    return (root / "prompts" / name).read_text(encoding="utf-8")


def _story_score(story, now):
    from datetime import datetime
    try:
        published = datetime.fromisoformat(story["published"])
        age_hours = max(0, (now - published).total_seconds() / 3600)
    except Exception:
        age_hours = 48
    freshness = max(0, 72 - age_hours)
    engagement = min(story.get("engagement", 0), 500)
    text = (story["title"] + " " + story["excerpt"]).lower()
    terms = (
        "celebrity", "hollywood", "influencer", "viral", "tiktok",
        "youtube", "internet", "reddit", "meme", "streamer",
        "billionaire", "weird", "social media", "pop culture"
    )
    relevance = sum(4 for term in terms if term in text)
    return freshness + engagement * 0.04 + relevance


def _json_safe(obj):
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2)


def run():
    settings, source_config = load_config()
    root = settings["root"]
    client = GeminiClient(settings["gemini_api_key"], settings["gemini_model"])
    now = datetime.now(timezone.utc)

    print("[1/5] Collecting public viral-story feeds...")
    stories = collect_stories(source_config)
    stories = [
        s for s in stories
        if acceptable_candidate(s, settings["max_story_age_hours"], now)
    ]
    stories.sort(key=lambda s: _story_score(s, now), reverse=True)
    stories = stories[:settings["candidate_limit"]]
    if not stories:
        raise RuntimeError("No recent stories found in configured RSS feeds.")

    print(f"[2/5] Screening {len(stories)} candidate stories in one research pass...")
    screening_prompt = (
        "You are a cautious story researcher. Assess every item in this input list. "
        "Return one JSON object with key 'items', containing one object per input item "
        "in the same order: index, suitable (boolean), summary, verified_facts_from_excerpt "
        "(array), uncertainties (array), comedy_potential (integer 0-10), reason. "
        "Do not assume headlines are true. A Reddit post alone is not proof of an allegation. "
        "Reject thin, stale, private-person, harmful-rumour or contextless stories. "
        "Only mark facts as verified if the supplied excerpt actually supports them."
    )
    try:
        screened_result = client.generate(
            screening_prompt, _json_safe(stories), temperature=0.2
        )
        assessments = screened_result.get("items", [])
    except Exception as exc:
        raise RuntimeError(f"Batch story screening failed: {exc}") from exc

    screened = []
    for item in assessments:
        try:
            idx = int(item.get("index", -1))
            if 0 <= idx < len(stories) and item.get("suitable") and int(item.get("comedy_potential", 0)) >= 6:
                story = dict(stories[idx])
                story["assessment"] = item
                screened.append(story)
        except (TypeError, ValueError):
            continue

    if not screened:
        raise RuntimeError("No candidate passed research screening. No weak scripts will be forced.")

    screened.sort(key=lambda s: _story_score(s, now), reverse=True)
    screened = screened[:max(settings["daily_script_target"] * 2, 6)]

    print("[3/5] Building premises, drafting and editing...")
    premise_prompt = _read_prompt(root, "premise-generator.md")
    writer_prompt = _read_prompt(root, "script-writer.md")
    critic_prompt = _read_prompt(root, "critic.md")
    punch_prompt = _read_prompt(root, "punch-up.md")
    comedy_science = (root / "docs/comedy-science.md").read_text(encoding="utf-8")[:6500]
    voice_bible = (root / "docs/voice-bible.md").read_text(encoding="utf-8")

    results = []
    used_urls = set()

    for story in screened:
        if len(results) >= settings["daily_script_target"]:
            break
        if story["url"] in used_urls:
            continue

        context = {
            "story": story,
            "editorial_direction": settings["voice"],
            "audience": settings["market_priority"],
            "comedy_science": comedy_science,
            "voice_bible": voice_bible
        }
        try:
            premises_result = client.generate(premise_prompt, _json_safe(context))
            options = premises_result.get("premises", [])
            if not options:
                continue
            # Prompt requests distinct premises; the first should be the strongest.
            selected_premise = options[0]

            draft = client.generate(writer_prompt, _json_safe({
                "story": story,
                "selected_premise": selected_premise,
                "word_target": f'{settings["min_words"]}-{settings["max_words"]}'
            }))
            if draft.get("status") == "REJECT":
                continue

            critique = client.generate(critic_prompt, _json_safe({
                "story": story, "draft": draft, "source_url": story["url"]
            }), temperature=0.2)

            try:
                critic_score = int(critique.get("score", 0))
            except (TypeError, ValueError):
                critic_score = 0

            if critique.get("verdict") != "PASS" or critic_score < settings["minimum_quality_score"]:
                revised = client.generate(punch_prompt, _json_safe({
                    "draft": draft,
                    "critique": critique,
                    "min_words": settings["min_words"],
                    "max_words": settings["max_words"]
                }))
                if revised.get("status") != "REVISED":
                    continue
                draft = revised
                final_critique = client.generate(critic_prompt, _json_safe({
                    "story": story, "draft": draft, "source_url": story["url"],
                    "instruction": "Final gate after rewrite. Be strict."
                }), temperature=0.2)
                try:
                    final_score = int(final_critique.get("score", 0))
                except (TypeError, ValueError):
                    final_score = 0
                if final_critique.get("verdict") != "PASS" or final_score < settings["minimum_quality_score"]:
                    print(f"[WARN] Rejected after punch-up: {story['title'][:65]}")
                    continue
                critique = final_critique

            script = draft.get("script", "").strip()
            count, issues = validate_script(
                script, settings["min_words"], settings["max_words"]
            )
            if issues:
                print(f"[WARN] Rejected draft: {' '.join(issues)}")
                continue

            results.append({
                "story": story,
                "premise": selected_premise,
                "script": script,
                "word_count": count,
                "critic": critique,
                "fact_risks": critique.get("fact_risks", [])
            })
            used_urls.add(story["url"])
        except Exception as exc:
            print(f"[WARN] Writing failed for '{story['title'][:60]}': {exc}")

    if not results:
        raise RuntimeError(
            "No script passed the minimum checks. Review logs and feeds; no filler will be generated."
        )

    print("[4/5] Saving research and scripts...")
    import json
    date = datetime.now().strftime("%Y-%m-%d")
    out_dir = root / "output" / date
    out_dir.mkdir(parents=True, exist_ok=True)

    research = [{
        "title": r["story"]["title"],
        "url": r["story"]["url"],
        "source": r["story"]["source"],
        "published": r["story"]["published"],
        "excerpt": r["story"]["excerpt"],
        "assessment": r["story"].get("assessment", {}),
        "premise": r["premise"]
    } for r in results]
    (out_dir / "research.json").write_text(
        _json_safe(research), encoding="utf-8"
    )

    lines = [
        f"# LaughLab AI — {date}",
        "",
        "> AI-assisted comedy drafts. Verify every factual claim and review every joke before recording. Model scores are not proof of laughter.",
        ""
    ]
    for i, item in enumerate(results, 1):
        lines += [
            f"## Script {i} — {item['story']['title']}",
            "",
            f"**Source:** [{item['story']['source']}]({item['story']['url']})  ",
            f"**Published:** {item['story']['published']}  ",
            f"**Length:** {item['word_count']} words  ",
            f"**Premise:** {item['premise'].get('premise', '')}",
            "",
            item["script"],
            "",
            "**Human review:** Check source context, factual claims, joke originality and spoken timing.",
            ""
        ]
        if item["fact_risks"]:
            lines += [
                "**Fact risks to resolve:**",
                *[f"- {risk}" for risk in item["fact_risks"]],
                ""
            ]

    (out_dir / "scripts.md").write_text("\\n".join(lines), encoding="utf-8")
    print(f"[5/5] Done. Saved {len(results)} script(s) to {out_dir.relative_to(root)}")
    if len(results) < settings["daily_script_target"]:
        print(
            f"[NOTE] Only {len(results)} passed. "
            "The system intentionally did not pad the batch."
        )
