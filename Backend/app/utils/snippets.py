import re


def make_snippet(text: str, query: str, window: int = 120):

    text_lower = text.lower()
    query_words = query.lower().split()

    # find first matching query term
    pos = -1
    match_word = None

    for word in query_words:
        p = text_lower.find(word)
        if p != -1:
            pos = p
            match_word = word
            break

    if pos == -1:
        snippet = text[:window]
    else:
        start = max(0, pos - window)
        end = min(len(text), pos + len(match_word) + window)
        snippet = text[start:end]

    # highlight all query words
    for word in query_words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        snippet = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", snippet)

    return snippet.strip()