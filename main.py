import codecs
from pathlib import Path
import sys

import requests


DEFAULT_URL = "https://eng.mipt.ru/why-mipt/"
DEFAULT_WORDS_FILE = Path("words.txt")
REQUEST_TIMEOUT = 15
CHUNK_SIZE = 16384
REQUEST_HEADERS = {
    "User-Agent": "mipt-msa-hw5/1.0"
}


def load_words_to_count(words_file):
    words_to_count = {}
    with open(words_file, "r", encoding="utf-8") as file:
        for line in file:
            word = line.strip()
            if word and word not in words_to_count:
                words_to_count[word] = 0
    return words_to_count


def iter_words_from_byte_chunks(chunks, encoding):
    decoder = codecs.getincrementaldecoder(encoding)(errors="ignore")
    tail = ""

    for chunk in chunks:
        text = tail + decoder.decode(chunk)
        if not text:
            continue

        parts = text.split()
        if text[-1].isspace():
            tail = ""
        elif parts:
            tail = parts.pop()
        else:
            tail = text

        for word in parts:
            yield word

    remainder = tail + decoder.decode(b"", final=True)
    if remainder:
        for word in remainder.split():
            yield word


def count_words_frequencies_from_chunks(chunks, encoding, words_to_count):
    frequencies = words_to_count.copy()
    for word in iter_words_from_byte_chunks(chunks, encoding):
        if word in frequencies:
            frequencies[word] += 1
    return frequencies


def count_words_frequencies(url, words_to_count):
    with requests.get(
        url,
        stream=True,
        timeout=REQUEST_TIMEOUT,
        headers=REQUEST_HEADERS,
    ) as response:
        response.raise_for_status()
        encoding = response.encoding or response.apparent_encoding or "utf-8"
        return count_words_frequencies_from_chunks(
            response.iter_content(chunk_size=CHUNK_SIZE),
            encoding,
            words_to_count,
        )


def count_word_frequencies(url, word):
    return count_words_frequencies(url, {word: 0})[word]


def main():
    words_to_count = load_words_to_count(DEFAULT_WORDS_FILE)
    try:
        frequencies = count_words_frequencies(DEFAULT_URL, words_to_count)
        print(frequencies)
    except requests.RequestException as exc:
        print(f"Failed to fetch source page: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()