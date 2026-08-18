"""Computes the content-based hash used to decide whether a node's cache is stale."""

import hashlib
import json

_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def hash_file(path):
    # Stream the file in fixed-size chunks instead of reading it whole, since
    # pipeline data files can be arbitrarily large; this keeps memory usage
    # O(1) in file size instead of O(file size).
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def compute_node_hash(innode_hashes, dep_paths):
    # A node's hash chains the hashes of its upstream nodes rather than
    # re-hashing their (potentially huge) output files directly. This still
    # transitively captures any change anywhere upstream, but each node only
    # ever hashes its own small dep files (e.g. source code), not the full
    # data flowing through the pipeline.
    dep_hashes = [hash_file(path) for path in dep_paths]
    payload = json.dumps({"innodes": innode_hashes, "deps": dep_hashes}).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
