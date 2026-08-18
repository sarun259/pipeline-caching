"""Parses a pipeline .conf file into a dict of NodeSpec objects.

Line format:
    <node name> [<innode1>,...,<innodek>] "<invocation>" <dep1>,<dep2>,...

Blank lines and lines starting with '#' are ignored.
"""

import re
from dataclasses import dataclass, field


@dataclass
class NodeSpec:
    name: str
    innodes: list = field(default_factory=list)
    invocation: str = ""
    deps: list = field(default_factory=list)


# name, then a bracketed innode list, then a quoted invocation, then a trailing deps list
_LINE_RE = re.compile(
    r'^(?P<name>\S+)\s*\[(?P<innodes>[^\]]*)\]\s*"(?P<invocation>[^"]*)"\s*(?P<deps>.*)$'
)


def _split_csv(text):
    text = text.strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",")]


def parse_conf(path):
    nodes = {}
    with open(path) as conf_file:
        for lineno, raw_line in enumerate(conf_file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            match = _LINE_RE.match(line)
            if match is None:
                raise ValueError(f"{path}:{lineno}: malformed line: {raw_line!r}")

            name = match["name"]
            if name in nodes:
                raise ValueError(f"{path}:{lineno}: duplicate node name {name!r}")

            invocation = match["invocation"]
            if "{OUTPUT}" not in invocation:
                raise ValueError(
                    f"{path}:{lineno}: invocation for node {name!r} has no {{OUTPUT}} placeholder"
                )

            nodes[name] = NodeSpec(
                name=name,
                innodes=_split_csv(match["innodes"]),
                invocation=invocation,
                deps=_split_csv(match["deps"]),
            )

    for spec in nodes.values():
        for innode in spec.innodes:
            if innode not in nodes:
                raise ValueError(
                    f"{path}: node {spec.name!r} depends on undefined node {innode!r}"
                )

    return nodes
