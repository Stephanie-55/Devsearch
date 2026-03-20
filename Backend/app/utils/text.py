def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50):
    """
    Splits text into overlapping chunks.
    """
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        start = end - overlap  # overlap for context

    return chunks