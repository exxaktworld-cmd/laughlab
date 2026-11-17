# Viral Research Method

1. Discover candidate stories from public RSS feeds.
2. Prefer recent stories with a clear source URL and enough context to understand what happened.
3. Deduplicate by normalized URL and title similarity.
4. Rank freshness, discussion signals when available, and fit with the channel's subject areas.
5. Ask Gemini to identify missing context and propose cautious research questions; do not let it invent facts.
6. Keep the source title, URL, excerpt and publication timestamp with each draft.
7. If the source is only a rumour or a single unverified post, reject it or clearly frame it as an unconfirmed online claim.
8. Use the actual article/source link in the output so the human editor can verify before recording.

## Important limits

RSS is a discovery layer, not proof. Headlines can be misleading. Reddit votes and comments are not always present in RSS and are not a representative poll. The script must not treat a viral post as confirmation of an allegation.
