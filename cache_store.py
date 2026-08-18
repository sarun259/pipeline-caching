"""On-disk cache of node outputs, with size-bounded LRU eviction.

Caches live at cache/<node>/<hash>. Rather than maintaining a separate
metadata file to track "last used" times, we reuse each cache file's mtime
for that purpose: touching it on a hit and setting it on creation. Scanning
the cache directory tree at startup is enough to reconstruct the full LRU
state, so the filesystem is the single source of truth.
"""

import os
import re
import time

_SIZE_UNITS = {"B": 1, "K": 1024, "KB": 1024, "M": 1024**2, "MB": 1024**2, "G": 1024**3, "GB": 1024**3}
_SIZE_RE = re.compile(r"^([0-9.]+)\s*([A-Za-z]*)$")


def parse_size(text):
    if isinstance(text, (int, float)):
        return int(text)
    match = _SIZE_RE.match(text.strip())
    if match is None:
        raise ValueError(f"invalid size: {text!r}")
    number, unit = match.groups()
    unit = unit.upper() or "B"
    if unit not in _SIZE_UNITS:
        raise ValueError(f"unknown size unit: {unit!r}")
    return int(float(number) * _SIZE_UNITS[unit])


class CacheEntry:
    __slots__ = ("path", "size", "last_used")

    def __init__(self, path, size, last_used):
        self.path = path
        self.size = size
        self.last_used = last_used


class CacheStore:
    def __init__(self, cache_dir, max_bytes):
        self.cache_dir = cache_dir
        self.max_bytes = max_bytes
        self.entries = {}  # (node, hash) -> CacheEntry
        os.makedirs(cache_dir, exist_ok=True)

    def scan(self):
        for node_name in os.listdir(self.cache_dir):
            node_dir = os.path.join(self.cache_dir, node_name)
            if not os.path.isdir(node_dir):
                continue
            for hash_ in os.listdir(node_dir):
                path = os.path.join(node_dir, hash_)
                stat = os.stat(path)
                self.entries[(node_name, hash_)] = CacheEntry(path, stat.st_size, stat.st_mtime)

    def get(self, node, hash_):
        entry = self.entries.get((node, hash_))
        if entry is None:
            return None
        entry.last_used = time.time()
        os.utime(entry.path, (entry.last_used, entry.last_used))
        return entry.path

    def add(self, node, hash_, produced_path):
        node_dir = os.path.join(self.cache_dir, node)
        os.makedirs(node_dir, exist_ok=True)
        dest = os.path.join(node_dir, hash_)
        os.replace(produced_path, dest)
        now = time.time()
        self.entries[(node, hash_)] = CacheEntry(dest, os.path.getsize(dest), now)
        return dest

    def total_size(self):
        return sum(entry.size for entry in self.entries.values())

    def evict_to_fit(self):
        total = self.total_size()
        if total <= self.max_bytes:
            return
        # oldest last_used first
        for key, entry in sorted(self.entries.items(), key=lambda kv: kv[1].last_used):
            if total <= self.max_bytes:
                break
            os.remove(entry.path)
            del self.entries[key]
            total -= entry.size
            print(f"[evict] {key[0]}/{key[1][:12]} ({entry.size} bytes)")
