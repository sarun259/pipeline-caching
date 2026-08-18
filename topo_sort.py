"""Graph utilities: finding which nodes a target depends on, and ordering them.

Both functions operate on a dict[name -> NodeSpec] as produced by conf_parser.parse_conf.
"""

from collections import deque


class GraphError(Exception):
    pass


def ancestors_including_self(nodes, target):
    """Every node that must be computed (in some order) to produce `target`."""
    if target not in nodes:
        raise GraphError(f"unknown target node: {target!r}")

    seen = set()
    stack = [target]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(nodes[name].innodes)
    return seen


def topological_order(nodes, subset):
    """Kahn's algorithm restricted to `subset`. Raises GraphError on a cycle."""
    in_degree = {name: 0 for name in subset}
    children = {name: [] for name in subset}
    for name in subset:
        for innode in nodes[name].innodes:
            children[innode].append(name)
            in_degree[name] += 1

    # sorted() makes the order deterministic given ties, which makes cache
    # behavior reproducible across runs and easier to reason about
    ready = deque(sorted(name for name in subset if in_degree[name] == 0))
    order = []
    while ready:
        name = ready.popleft()
        order.append(name)
        for child in sorted(children[name]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                ready.append(child)

    if len(order) != len(subset):
        raise GraphError("dependency graph contains a cycle")
    return order
