"""Parity tests between confme's YAML parser and PyYAML's ``safe_load``.

PyYAML is only a development dependency used as reference implementation; confme itself must not import it.
"""

import datetime
import math
import random
import subprocess
import sys
from typing import Any

import pytest

from confme.source_backend.yaml_parser import ParserError, load

yaml = pytest.importorskip("yaml")

VALID_DOCUMENTS = [
    'name: "Database Application"\ndatabase:\n    host: "localhost"\n    port: 5000\n',
    "servers:\n  - name: a\n    ports:\n      - 80\n      - 443\n  - name: b\n",
    "key:\n- a\n- b\nother: 1\n",
    "- - 1\n  - 2\n- - 3\n",
    "    indented: 1\n    root: 2\n",
    "a:\nb:\n- \n",
    "a: 1 # c\n# full\nb: 'x # y'\ncolor: #fff\nurl: http://x.com/#frag\n",
    "msg: don't panic\nname: O'Brien\nsize: 5\"\nmixed: it's 'quoted' text\n",
    "desc: |\n  It's a test.\n  # not a comment\n",
    "a: \"x\"#c\nb: 'y' # c\n",
    "a: >-\n  part one\n  part two\n\n  second paragraph\n",
    "a: >\n  normal\n    indented\n  normal again\n\n  last\n",
    "a: |+\n  x\n\nb: |-\n  y\n\nc: |\n  z\n\n\n",
    "a: |2\n   x\nb: >2-\n   y\n   z\n",
    "a: |\n  x",
    "- |\n  item\n- >\n  folded\n  item\n",
    "base: &base\n  host: localhost\ndev:\n  <<: *base\n  port: 5433\n",
    "x: &a {k: 1}\ny: &b {k: 2, j: 3}\nz:\n  <<: [*a, *b]\n  m: 0\n",
    "a: &p 5432\nb: *p\nc: &l [1, 2]\nd: *l\n&k key: value\ne: *k\n",
    "a: &x\n  !!str k: v\n",
    "a: !!str 123\nb: !!int '42'\nc: !!float 1\nd: !!bool yes\ne: !!null x\nf: !!binary aGVsbG8=\n",
    "a: !!set {x, y}\nb: !!omap [a: 1, b: 2]\nc: !<tag:yaml.org,2002:str> 5\nd: ! 12\n",
    "%YAML 1.1\n%TAG !e! tag:yaml.org,2002:\n---\na: !e!str 1\n",
    "a: this is a long\n  plain scalar\n\n  next paragraph\n",
    "a: \"quoted\n  scalar \\\n  continued\"\nb: 'single\n\n  quoted'\n",
    "- multi\n  line item\n- next\n",
    '{"name": "x", "db": {"port": 5000}}\n',
    'a: {"k":1, b, c: }\nd: [a: 1, b, ]\ne: [\n  1,\n  2  # comment\n]\n',
    "a: [a:1]\nb: {a:1}\nc: [http://x.com/a, b]\n",
    "? a\n: b\n? |\n  block key\n: v\n",
    "\ufeffname: x\r\nport: 1\r\n",
    'a: "\\e\\a\\N\\_\\L\\P\\v\\0\\ \\/\\x41\\u00e9\\U0001F600"\n',
    "a: 0755\nb: 0o17\nc: 0b101\nd: 0x1A\ne: -0x1A\nf: 1_000\ng: +12\nh: -0\ni: 00\nj: 08\n",
    "a: 1e3\nb: 1.0e3\nc: 1.5e-3\nd: 1.\ne: .5\nf: -.5\ng: 1_000.5\nh: .inf\ni: -.Inf\nj: .NaN\n",
    "a: 12:30\nb: 1:20:30\nc: 190:20:30.15\n",
    "a: 2024-01-01\nb: 2001-12-14t21:59:43.10-05:00\nc: 2001-12-14 21:59:43.10 -5\nd: 2001-12-15T02:59:43.1Z\n",
    "a: yes\nb: No\nc: ON\nd: off\ne: y\nf: n\ng: tRue\n",
    "on: 1\nyes: 2\n1: a\n1.5: b\n0x10: c\nnull: d\n~: e\n2024-01-01: f\n'<<': g\n",
    "a: '123'\nb: \"true\"\nc: '~'\nd: x#y\ne: -5\nf: -x\ng: ?x\nh: :x\n",
    "---\na: 1\n...\n",
    "--- |\n  text\n",
    "",
    "# only a comment\n",
    "~\n",
    "- a\n",
]

INVALID_DOCUMENTS = [
    "a: *undefined\n",
    "a: &x 1\nb: &x 2\n",
    "a: !custom x\n",
    "a: b\n  c: d\n",
    "a: b: c\n",
    "a: - b\n",
    "[1, 2]: x\n",
    "a: [1, , 2]\n",
    "a: [1\n",
    "a: 1\n\tb: 2\n",
    "a: \x07\n",
    "a: 1\n---\nb: 2\n",
    "--- a: 1\n",
    "- a\nb: 1\n",
    "a: 1\n- b\n",
    "a:\n  - x\n  y: 1\n",
    "a\nb: c\n",
    'a: "\\xZZ"\n',
    'a: "C:\\path"\n',
    'a: "unterminated\n',
    "a: [x]]\n",
    "a: @x\n",
    "a: %x\n",
    "a: |0\n  x\n",
    "a: |x\n",
    "*a: 1\n",
    "a: 2024-13-45\n",
]

# Inputs rejected by PyYAML but accepted by confme (YAML 1.2 allows them, or the value is unambiguous).
LENIENT_DOCUMENTS = {
    "a:\tb\n": {"a": "b"},
    "a: x\ty\n": {"a": "x\ty"},
    "a: 1\n  \t\nb: 2\n": {"a": 1, "b": 2},
    "a: {: v}\n": {"a": {None: "v"}},
    "...\na: 1\n": {"a": 1},
    "a: =\n": {"a": "="},
}


def _equal(ours: Any, reference: Any) -> bool:
    if type(ours) is not type(reference):
        return False
    if isinstance(ours, float):
        return ours == reference or (math.isnan(ours) and math.isnan(reference))
    if isinstance(ours, dict):
        return list(ours) == list(reference) and all(_equal(ours[k], reference[k]) for k in ours)
    if isinstance(ours, (list, tuple)):
        return len(ours) == len(reference) and all(_equal(a, b) for a, b in zip(ours, reference))
    return ours == reference


@pytest.mark.parametrize("text", VALID_DOCUMENTS)
def test_matches_pyyaml(text: str):
    assert _equal(load(text), yaml.safe_load(text))


@pytest.mark.parametrize("text", INVALID_DOCUMENTS)
def test_rejects_documents_rejected_by_pyyaml(text: str):
    with pytest.raises(Exception):  # noqa: B017 - PyYAML raises YAMLError or e.g. ValueError for invalid dates
        yaml.safe_load(text)
    with pytest.raises(ParserError):
        load(text)


@pytest.mark.parametrize(("text", "expected"), LENIENT_DOCUMENTS.items())
def test_lenient_where_pyyaml_fails(text: str, expected: Any):
    assert load(text) == expected


WORDS = [
    "a", "b c", "it's", 'say "hi"', "x: y", "#hash", "a #b", "- dash", "?q", "yes", "No", "~", "null", "123", "0755",
    "1e3", "12:30", "2024-01-01", "", " lead", "trail ", "multi\nline", "line\n\nbreaks\n", "tab\there", "ünïcödé",
    "emoji 😀", "back\\slash", "[bracket]", "{brace}", "a,b", "*star", "&amp", "!bang", "%pct", "@at", "`tick",
    "|pipe", ">gt", "long " * 12, "<<", "=", "---", "...", "C:\\path", "http://x/y?z=1#f",
]  # fmt: skip


def _random_object(rng: random.Random, depth: int = 0) -> Any:
    kind = rng.randrange(4) if depth < 4 else 3
    if kind == 0:
        return [_random_object(rng, depth + 1) for _ in range(rng.randrange(4))]
    if kind == 1:
        return {
            rng.choice([*WORDS, 1, 2.5, True, None]): _random_object(rng, depth + 1) for _ in range(rng.randrange(4))
        }
    if kind == 2:
        return {rng.choice(WORDS): _random_object(rng, depth + 1) for _ in range(rng.randrange(1, 4))}
    return rng.choice(
        [
            rng.randint(-(10**6), 10**6),
            rng.choice([0.5, -1.25, 1e20, float("inf"), 0.0]),
            rng.choice([True, False, None]),
            datetime.date(2020, rng.randint(1, 12), rng.randint(1, 28)),
            rng.choice(WORDS),
            rng.choice(WORDS),
        ]
    )


def test_matches_pyyaml_on_emitted_documents():
    rng = random.Random(42)
    for _ in range(1000):
        shared = _random_object(rng)
        data = {"root": _random_object(rng), "x": shared, "y": [shared, {"z": shared}]}
        text = yaml.safe_dump(
            data,
            default_flow_style=rng.choice([False, True, None]),
            width=rng.choice([10, 30, 80, 1000]),
            canonical=rng.random() < 0.15,
            allow_unicode=rng.random() < 0.5,
            default_style=rng.choice([None, None, None, "'", '"', "|", ">"]),
            indent=rng.choice([2, 3, 4]),
            explicit_start=rng.random() < 0.2,
            explicit_end=rng.random() < 0.1,
        )
        assert _equal(load(text), yaml.safe_load(text)), text


def test_confme_does_not_import_pyyaml():
    code = "import sys, confme, confme.source_backend; print('yaml' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "False"
