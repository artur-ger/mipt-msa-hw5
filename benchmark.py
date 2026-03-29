import time
import tracemalloc

import main


TEXT_REPEAT_COUNT = 300
SEED_WORD_COUNT = 500
FILLER_WORDS = [
    "mipt",
    "science",
    "education",
    "students",
    "research",
] * 20


def load_raw_words(words_file):
    with open(words_file, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def build_benchmark_payload(raw_words):
    sample = raw_words[:SEED_WORD_COUNT] + FILLER_WORDS
    text = (" ".join(sample) + " ") * TEXT_REPEAT_COUNT
    return text.encode("utf-8")


def baseline_count_words_frequencies(payload, raw_words):
    text = payload.decode("utf-8")
    frequencies = {}
    for word in raw_words:
        count = 0
        for token in text.split():
            if token == word:
                count += 1
        frequencies[word] = count
    return frequencies


def iter_payload_chunks(payload):
    for offset in range(0, len(payload), main.CHUNK_SIZE):
        yield payload[offset:offset + main.CHUNK_SIZE]


def optimized_count_words_frequencies(payload, raw_words):
    words_to_count = {word: 0 for word in raw_words}
    return main.count_words_frequencies_from_chunks(
        iter_payload_chunks(payload),
        "utf-8",
        words_to_count,
    )


def measure(function, *args):
    tracemalloc.start()
    start = time.perf_counter()
    result = function(*args)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def main_benchmark():
    raw_words = load_raw_words("words.txt")
    unique_words = list(dict.fromkeys(raw_words))
    payload = build_benchmark_payload(raw_words)

    baseline_result, baseline_time, baseline_peak = measure(
        baseline_count_words_frequencies,
        payload,
        unique_words,
    )
    optimized_result, optimized_time, optimized_peak = measure(
        optimized_count_words_frequencies,
        payload,
        unique_words,
    )

    if baseline_result != optimized_result:
        raise RuntimeError("Optimized implementation changed the resulting frequencies.")

    print(f"words_total={len(raw_words)}")
    print(f"words_unique={len(unique_words)}")
    print(f"payload_bytes={len(payload)}")
    print(f"baseline_time={baseline_time:.4f}")
    print(f"optimized_time={optimized_time:.4f}")
    print(f"speedup={baseline_time / optimized_time:.2f}x")
    print(f"baseline_peak={baseline_peak}")
    print(f"optimized_peak={optimized_peak}")
    print(f"memory_reduction={baseline_peak / optimized_peak:.2f}x")


if __name__ == "__main__":
    main_benchmark()