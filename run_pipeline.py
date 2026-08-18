#!/usr/bin/env python3
"""Core driver: runs a computation DAG described by a .conf file, caching each
node's output and invalidating a node's cache iff its dependencies changed.
"""

import argparse
import os
import subprocess
import tempfile

from cache_store import CacheStore, parse_size
from conf_parser import parse_conf
from hashing import compute_node_hash
from topo_sort import ancestors_including_self, topological_order


def _substitute(invocation, input_paths, output_path):
    text = invocation
    for i, path in enumerate(input_paths, start=1):
        text = text.replace(f"{{INPUT{i}}}", path)
    return text.replace("{OUTPUT}", output_path)


def _invoke(invocation, input_paths, output_path, cwd):
    command = _substitute(invocation, input_paths, output_path)
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"invocation failed (exit {result.returncode}): {command}")


def run_pipeline(conf_path, target, max_memory, redo=False):
    conf_dir = os.path.dirname(os.path.abspath(conf_path)) or "."
    nodes = parse_conf(conf_path)

    needed = ancestors_including_self(nodes, target)
    order = topological_order(nodes, needed)

    cache = CacheStore(os.path.join(conf_dir, "cache"), parse_size(max_memory))
    cache.scan()

    outputs, hashes = {}, {}
    with tempfile.TemporaryDirectory(dir=cache.cache_dir) as tmp_dir:
        for name in order:
            spec = nodes[name]
            dep_paths = [os.path.join(conf_dir, dep) for dep in spec.deps]
            node_hash = compute_node_hash([hashes[i] for i in spec.innodes], dep_paths)
            hashes[name] = node_hash

            cached_path = None if redo else cache.get(name, node_hash)
            if cached_path is not None:
                print(f"[hit]  {name} ({node_hash[:12]})")
                outputs[name] = cached_path
                continue

            print(f"[run]  {name} ({node_hash[:12]})")
            tmp_output = os.path.join(tmp_dir, f"{name}_{node_hash[:12]}")
            _invoke(spec.invocation, [outputs[i] for i in spec.innodes], tmp_output, conf_dir)
            outputs[name] = cache.add(name, node_hash, tmp_output)

    cache.evict_to_fit()
    return outputs[target]


def main():
    parser = argparse.ArgumentParser(description="Run a cached computation pipeline.")
    parser.add_argument("conf", help="path to the .conf file describing the DAG")
    parser.add_argument("target", help="name of the node to build")
    parser.add_argument("max_memory", help="cache size budget, e.g. 500MB, 2GB, or a plain byte count")
    parser.add_argument("--redo", action="store_true", help="always re-run every node, ignoring caches")
    args = parser.parse_args()

    result_path = run_pipeline(args.conf, args.target, args.max_memory, redo=args.redo)
    print(f"\ntarget {args.target!r} -> {result_path}")


if __name__ == "__main__":
    main()
