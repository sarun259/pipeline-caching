"""Runs the example pipeline several times to demonstrate that caching
behaves correctly: hits on repeat runs, invalidation on a dep change,
--redo forcing recomputation, and LRU eviction under a tight budget.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_pipeline import run_pipeline

EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(EXAMPLE_DIR, "example.conf")
SQUARE_SCRIPT = os.path.join(EXAMPLE_DIR, "scripts", "square.py")
CACHE_DIR = os.path.join(EXAMPLE_DIR, "cache")


def section(title):
    print(f"\n=== {title} ===")


def main():
    if os.path.isdir(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)

    section("1) fresh run: every node should be a cache miss ([run])")
    result_a = run_pipeline(CONF, "merged", "10MB")

    section("2) repeat run: every node should be a cache hit ([hit]) and reuse the same file")
    result_b = run_pipeline(CONF, "merged", "10MB")
    assert result_a == result_b, "expected the second run to reuse the exact same cache file"

    section("3) edit square.py: only 'squared' and 'merged' should rerun")
    original_source = open(SQUARE_SCRIPT).read()
    edited_source = original_source.replace("** 2", "** 3")  # square -> cube
    assert edited_source != original_source, "expected the edit to actually change square.py"
    try:
        open(SQUARE_SCRIPT, "w").write(edited_source)
        result_c = run_pipeline(CONF, "merged", "10MB")
        assert result_c != result_b, "expected a new cache entry once square.py's content changed"
    finally:
        open(SQUARE_SCRIPT, "w").write(original_source)

    section("4) --redo: every node reruns regardless of cache state")
    run_pipeline(CONF, "merged", "10MB", redo=True)

    section("5) tiny max_memory: forces LRU eviction of (almost) everything")
    run_pipeline(CONF, "merged", "1B", redo=True)
    remaining = sum(len(files) for _, _, files in os.walk(CACHE_DIR))
    print(f"cache entries remaining under a ~0-byte budget: {remaining}")
    assert remaining == 0, "expected eviction to remove every cache entry under a 1-byte budget"

    print("\nall demo checks passed")


if __name__ == "__main__":
    main()
