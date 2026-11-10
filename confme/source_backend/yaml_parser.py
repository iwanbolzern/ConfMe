"""Dependency-free YAML parser compatible with PyYAML's ``safe_load``.

Supports the YAML 1.1 features found in configuration files: block and flow collections, plain, quoted and block
scalars, comments, anchors, aliases, merge keys (``<<``), the standard tags (``!!str``, ``!!int``, ``!!binary``, ...)
and PyYAML's implicit type resolution (e.g. ``yes`` -> ``True``, ``0755`` -> ``493``, ``2024-01-01`` -> ``date``).
"""

import base64
import binascii
import datetime
import re
from typing import Any
from urllib.parse import unquote

from confme.utils.base_exception import ConfmeException


class ParserError(ConfmeException):
    """Raised when a YAML document cannot be parsed."""


_TAG_PREFIX = "tag:yaml.org,2002:"
_STR = _TAG_PREFIX + "str"
_INT = _TAG_PREFIX + "int"
_FLOAT = _TAG_PREFIX + "float"
_BOOL = _TAG_PREFIX + "bool"
_NULL = _TAG_PREFIX + "null"
_TIMESTAMP = _TAG_PREFIX + "timestamp"
_BINARY = _TAG_PREFIX + "binary"
_MERGE = _TAG_PREFIX + "merge"
_SEQ = _TAG_PREFIX + "seq"
_MAP = _TAG_PREFIX + "map"
_SET = _TAG_PREFIX + "set"
_OMAP = _TAG_PREFIX + "omap"
_PAIRS = _TAG_PREFIX + "pairs"


class _MergeKey:
    """Marker for the merge key ``<<``."""


_MERGE_KEY = _MergeKey()

# Implicit resolvers of YAML 1.1 as used by PyYAML.
_NULL_RE = re.compile(r"~|null|Null|NULL|")
_BOOL_RE = re.compile(r"yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF")
_INT_RE = re.compile(
    r"[-+]?0b[0-1_]+|[-+]?0[0-7_]+|[-+]?(?:0|[1-9][0-9_]*)|[-+]?0x[0-9a-fA-F_]+|[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+"
)
_FLOAT_RE = re.compile(
    r"[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?"
    r"|[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN)"
)
_IMPLICIT_TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
    r"|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?"
    r"(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?"
)
_TIMESTAMP_RE = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{1,2})-(?P<day>[0-9]{1,2})"
    r"(?:(?:[Tt]|[ \t]+)(?P<hour>[0-9]{1,2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]*))?"
    r"(?:[ \t]*(?P<tz>Z|(?P<tz_sign>[-+])(?P<tz_hour>[0-9]{1,2})(?::(?P<tz_minute>[0-9]{2}))?))?)?"
)
_BOOL_VALUES = {"yes": True, "no": False, "true": True, "false": False, "on": True, "off": False}

_NON_PRINTABLE = re.compile("[^\x09\x0a\x0d\x20-\x7e\x85\xa0-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")
_ANCHOR_CHARS = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_")
_TAG_URI_CHARS = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-;/?:@&=+$,_.!~*'()[]%")
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_ESCAPES = {
    "0": "\0",
    "a": "\x07",
    "b": "\x08",
    "t": "\x09",
    "\t": "\x09",
    "n": "\x0a",
    "v": "\x0b",
    "f": "\x0c",
    "r": "\x0d",
    "e": "\x1b",
    " ": " ",
    '"': '"',
    "/": "/",
    "\\": "\\",
    "N": "\x85",
    "_": "\xa0",
    "L": "\u2028",
    "P": "\u2029",
}
_ESCAPE_CODES = {"x": 2, "u": 4, "U": 8}

_WS = " \t"
_WS_OR_EOL = " \t\n\0"
_FLOW_INDICATORS = ",[]{}"
_PLAIN_START_INDICATORS = "\0 \t\n-?:,[]{}#&*!|>'\"%@`"


def load(text: str, name: str | None = None) -> Any:
    """Parse a single YAML document like ``yaml.safe_load`` does.

    :param text: YAML content
    :param name: optional source name (e.g. file path) used in error messages
    :return: the constructed Python object (None for an empty document)
    """
    return _Parser(text, name).parse_stream()


def _resolve(text: str) -> str:
    """Implicit tag of a plain scalar."""
    if _NULL_RE.fullmatch(text):
        return _NULL
    if _BOOL_RE.fullmatch(text):
        return _BOOL
    if _INT_RE.fullmatch(text):
        return _INT
    if _FLOAT_RE.fullmatch(text):
        return _FLOAT
    if _IMPLICIT_TIMESTAMP_RE.fullmatch(text):
        return _TIMESTAMP
    if text == "<<":
        return _MERGE
    return _STR


def _sexagesimal(value: str, number: type) -> Any:
    result = number(0)
    for part in value.split(":"):
        result = result * 60 + number(part)
    return result


def _construct_int(text: str) -> int:
    value = text.replace("_", "")
    sign = -1 if value.startswith("-") else 1
    if value[:1] in ("+", "-"):
        value = value[1:]
    if value == "0":
        return 0
    if value.startswith("0b"):
        return sign * int(value[2:], 2)
    if value.startswith("0x"):
        return sign * int(value[2:], 16)
    if value.startswith("0"):
        return sign * int(value, 8)
    if ":" in value:
        return sign * _sexagesimal(value, int)
    return sign * int(value)


def _construct_float(text: str) -> float:
    value = text.replace("_", "").lower()
    sign = -1.0 if value.startswith("-") else 1.0
    if value[:1] in ("+", "-"):
        value = value[1:]
    if value == ".inf":
        return sign * float("inf")
    if value == ".nan":
        return float("nan")
    if ":" in value:
        return sign * _sexagesimal(value, float)
    return sign * float(value)


def _construct_timestamp(text: str) -> datetime.date:
    match = _TIMESTAMP_RE.fullmatch(text)
    if match is None:
        raise ValueError(f"invalid timestamp {text!r}")
    values = match.groupdict()
    year, month, day = int(values["year"]), int(values["month"]), int(values["day"])
    if not values["hour"]:
        return datetime.date(year, month, day)
    fraction = int((values["fraction"] or "")[:6].ljust(6, "0"))
    tzinfo = None
    if values["tz_sign"]:
        delta = datetime.timedelta(hours=int(values["tz_hour"]), minutes=int(values["tz_minute"] or 0))
        tzinfo = datetime.timezone(-delta if values["tz_sign"] == "-" else delta)
    elif values["tz"]:
        tzinfo = datetime.timezone.utc
    hour, minute, second = int(values["hour"]), int(values["minute"]), int(values["second"])
    return datetime.datetime(year, month, day, hour, minute, second, fraction, tzinfo=tzinfo)


class _Parser:
    """Recursive descent parser that constructs Python objects while parsing."""

    def __init__(self, text: str, name: str | None) -> None:
        if text.startswith("\ufeff"):
            text = text[1:]
        self.name = name
        self.src = text.replace("\r\n", "\n").replace("\r", "\n") + "\0"
        self.pos = 0
        self.anchors: dict[str, Any] = {}
        self.tag_handles = {"!": "!", "!!": _TAG_PREFIX}
        invalid = _NON_PRINTABLE.search(self.src, 0, len(self.src) - 1)
        if invalid:
            raise self.error(f"special characters are not allowed (found {invalid.group()!r})", invalid.start())

    # ------------------------------------------------------------------ helpers

    def error(self, message: str, pos: int | None = None) -> ParserError:
        pos = self.pos if pos is None else min(pos, len(self.src) - 1)
        line = self.src.count("\n", 0, pos) + 1
        column = pos - self.line_start(pos) + 1
        where = f'in "{self.name}", ' if self.name else ""
        return ParserError(f"{message} ({where}line {line}, column {column})")

    def ch(self, offset: int = 0) -> str:
        index = self.pos + offset
        return self.src[index] if index < len(self.src) else "\0"

    def line_start(self, pos: int) -> int:
        return self.src.rfind("\n", 0, pos) + 1

    def line_end(self, pos: int) -> int:
        end = self.src.find("\n", pos)
        return end if end != -1 else len(self.src) - 1

    def column(self, pos: int | None = None) -> int:
        pos = self.pos if pos is None else pos
        return pos - self.line_start(pos)

    def skip_inline_ws(self) -> None:
        while self.src[self.pos] in _WS:
            self.pos += 1

    def at_line_end(self) -> bool:
        return self.src[self.pos] in "\n\0#"

    def is_indicator(self, char: str) -> bool:
        """True if the current char is the given indicator followed by white space."""
        return self.src[self.pos] == char and self.ch(1) in _WS_OR_EOL

    def is_document_marker(self, pos: int | None = None) -> bool:
        pos = self.pos if pos is None else pos
        return (
            (pos == 0 or self.src[pos - 1] == "\n")
            and self.src[pos : pos + 3] in ("---", "...")
            and (pos + 3 >= len(self.src) or self.src[pos + 3] in _WS_OR_EOL)
        )

    def skip_blank_block(self) -> None:
        """Skip white space, comments and line breaks in block context and check the indentation for tabs."""
        crossed_line = self.pos == 0 or self.src[self.pos - 1] == "\n"
        while True:
            char = self.src[self.pos]
            if char in _WS:
                self.pos += 1
            elif char == "#":
                self.pos = self.line_end(self.pos)
            elif char == "\n":
                self.pos += 1
                crossed_line = True
            else:
                break
        if crossed_line and char != "\0":
            indentation = self.src[self.line_start(self.pos) : self.pos]
            if "\t" in indentation:
                raise self.error(
                    "found a tab character where an indentation space is expected",
                    self.line_start(self.pos) + indentation.index("\t"),
                )

    def skip_blank_flow(self, start: int) -> None:
        """Skip white space, comments and line breaks inside a flow collection."""
        while True:
            char = self.src[self.pos]
            if char in _WS:
                self.pos += 1
            elif char == "#":
                self.pos = self.line_end(self.pos)
            elif char == "\n":
                self.pos += 1
                if self.is_document_marker():
                    raise self.error("found unexpected document separator inside a flow collection")
            elif char == "\0":
                raise self.error("found unexpected end of stream while parsing a flow collection", start)
            else:
                return

    # ------------------------------------------------------------------ stream

    def parse_stream(self) -> Any:
        has_directives = self.parse_directives()
        self.skip_blank_block()
        while self.is_document_marker() and self.src.startswith("...", self.pos):
            self.pos += 3
            self.skip_blank_block()
        if self.src[self.pos] == "\0":
            if has_directives:
                raise self.error("expected '<document start>', but found end of stream")
            return None

        if self.is_document_marker() and self.src.startswith("---", self.pos):
            self.pos += 3
            value = self.parse_block_node(-1, inline_block=False, indentless_seq=False)
        elif has_directives:
            raise self.error("expected '<document start>', but found other content")
        else:
            value = self.parse_block_node(-1, inline_block=True, indentless_seq=False)

        self.skip_blank_block()
        if self.is_document_marker() and self.src.startswith("...", self.pos):
            while self.is_document_marker() and self.src.startswith("...", self.pos):
                self.pos += 3
                self.skip_inline_ws()
                if not self.at_line_end():
                    raise self.error("expected a comment or a line break after the document end marker")
                self.skip_blank_block()
        if self.src[self.pos] != "\0":
            if self.is_document_marker() or (self.src[self.pos] == "%" and self.column() == 0):
                raise self.error("expected a single document in the stream, but found another document")
            raise self.error("expected the end of the document, but found unexpected content (check the indentation)")
        return value

    def parse_directives(self) -> bool:
        found = False
        yaml_version_seen = False
        while True:
            self.skip_blank_block()
            if self.src[self.pos] != "%" or self.column() != 0:
                return found
            found = True
            start = self.pos
            parts = self.src[self.pos + 1 : self.line_end(self.pos)].split("#", 1)[0].split()
            if parts and parts[0] == "YAML":
                if yaml_version_seen:
                    raise self.error("found duplicate YAML directive", start)
                yaml_version_seen = True
                if len(parts) != 2 or not re.fullmatch(r"[0-9]+\.[0-9]+", parts[1]):
                    raise self.error("expected a version number in the YAML directive", start)
                if parts[1].split(".")[0] != "1":
                    raise self.error("found incompatible YAML document (version 1.* is required)", start)
            elif parts and parts[0] == "TAG":
                if len(parts) != 3 or not re.fullmatch(r"!(?:[0-9A-Za-z_-]*!)?", parts[1]):
                    raise self.error("expected a tag handle and prefix in the TAG directive", start)
                if parts[1] in self.tag_handles and parts[1] not in ("!", "!!"):
                    raise self.error(f"found duplicate tag handle {parts[1]!r}", start)
                self.tag_handles[parts[1]] = parts[2]
            self.pos = self.line_end(self.pos)

    # ------------------------------------------------------------------ block context

    def parse_block_node(
        self, indent: int, inline_block: bool, indentless_seq: bool, outer_props: tuple | None = None
    ) -> Any:
        """Parse a node in block context.

        :param indent: indentation of the parent block collection (-1 for the document root)
        :param inline_block: whether a block collection may start at the current position of the line
        :param indentless_seq: whether a block sequence at the parent's indentation belongs to this node
        :param outer_props: properties (anchor, tag) found on a previous line
        """
        self.skip_inline_ws()
        if self.at_line_end():
            self.skip_blank_block()
            if self.src[self.pos] != "\0" and not self.is_document_marker():
                column = self.column()
                if column > indent or (indentless_seq and column == indent and self.is_indicator("-")):
                    return self.parse_block_node(indent, True, False, outer_props)
            return self.construct_empty(outer_props)

        start = self.pos
        props = self.scan_properties()
        if props is not None and self.at_line_end():
            if outer_props is not None:
                raise self.error("found duplicate node properties", start)
            return self.parse_block_node(indent, inline_block, indentless_seq, props)

        if self.src[self.pos] in "-?:" and self.ch(1) in _WS_OR_EOL:
            indicator = self.src[self.pos]
            if props is not None or not inline_block:
                kind = {"-": "sequence entries", "?": "mapping keys", ":": "mapping values"}[indicator]
                raise self.error(f"{kind} are not allowed here")
            if indicator == "-":
                value = self.parse_block_sequence(self.column())
            else:
                value = self.parse_block_mapping(self.column())
            return self.construct_collection(value, outer_props, start)

        colon = self.find_implicit_key_value(self.pos)
        if colon is not None:
            # properties in front of an implicit key belong to the key, outer properties to the mapping
            if not inline_block:
                raise self.error("mapping values are not allowed here", colon)
            self.pos = start
            return self.construct_collection(self.parse_block_mapping(self.column()), outer_props, start)

        if props is not None and outer_props is not None:
            raise self.error("found duplicate node properties", start)
        return self.parse_inline_node(indent, props if props is not None else outer_props)

    def parse_inline_node(self, indent: int, props: tuple | None) -> Any:
        """Parse a scalar, alias or flow collection that starts on the current line (block context)."""
        start = self.pos
        char = self.src[self.pos]
        if char in "|>":
            text = self.scan_block_scalar(indent)
            return self.finish_scalar(text, False, props, start)
        if char == "*":
            if props is not None:
                raise self.error("an alias node cannot have properties", start)
            value = self.parse_alias()
        elif char in "[{":
            value = self.construct_collection(self.parse_flow_collection(), props, start)
        elif char in "'\"":
            value = self.finish_scalar(self.scan_quoted(), False, props, start)
        elif self.can_start_plain(flow=False):
            value = self.finish_scalar(self.scan_plain(indent, flow=False), True, props, start)
        else:
            raise self.error(f"found character {char!r} that cannot start any token")
        self.skip_inline_ws()
        if not self.at_line_end():
            if self.is_indicator(":"):
                raise self.error("mapping values are not allowed here")
            raise self.error(f"expected the end of the line, but found {self.src[self.pos]!r}")
        return value

    def parse_block_sequence(self, column: int) -> list[Any]:
        items: list[Any] = []
        while True:
            self.pos += 1  # '-'
            items.append(self.parse_block_node(column, inline_block=True, indentless_seq=False))
            self.skip_blank_block()
            if self.src[self.pos] == "\0" or self.is_document_marker():
                return items
            next_column = self.column()
            if next_column < column or (next_column == column and not self.is_indicator("-")):
                return items
            if next_column > column:
                raise self.error("bad indentation of a sequence entry")

    def parse_block_mapping(self, column: int) -> dict[Any, Any]:
        entries: list[tuple[Any, Any, int]] = []
        while True:
            entry_pos = self.pos
            if self.is_indicator("?"):
                self.pos += 1
                key = self.check_key(self.parse_block_node(column, True, True), entry_pos)
                self.skip_blank_block()
                if self.src[self.pos] != "\0" and self.column() == column and self.is_indicator(":"):
                    self.pos += 1
                    value = self.parse_block_node(column, True, True)
                else:
                    value = None
            elif self.is_indicator(":"):
                self.pos += 1
                key = None
                value = self.parse_block_node(column, True, True)
            else:
                key = self.parse_implicit_key()
                value = self.parse_block_node(column, inline_block=False, indentless_seq=True)
            entries.append((key, value, entry_pos))

            self.skip_blank_block()
            if self.src[self.pos] == "\0" or self.is_document_marker():
                break
            next_column = self.column()
            if next_column < column:
                break
            if next_column > column:
                raise self.error("bad indentation of a mapping entry")
            if self.is_indicator("-"):
                raise self.error("expected a mapping entry, but found a sequence entry")
        return self.build_mapping(entries)

    def parse_implicit_key(self) -> Any:
        start = self.pos
        props = self.scan_properties()
        char = self.src[self.pos]
        if char == "*":
            if props is not None:
                raise self.error("an alias node cannot have properties", start)
            key = self.parse_alias()
        elif char in "[{":
            key = self.construct_collection(self.parse_flow_collection(), props, start)
        elif char in "'\"":
            key = self.finish_scalar(self.scan_quoted(), False, props, start, as_key=True)
        elif char in "|>" or not self.can_start_plain(flow=False):
            raise self.error(f"found character {char!r} that cannot start a mapping key")
        else:
            key = self.finish_scalar(self.scan_plain(self.column(start), flow=False), True, props, start, as_key=True)
        self.skip_inline_ws()
        if "\n" in self.src[start : self.pos] or not self.is_indicator(":"):
            raise self.error("could not find expected ':' (mapping keys must be on a single line)", start)
        self.pos += 1
        return self.check_key(key, start)

    def find_implicit_key_value(self, pos: int) -> int | None:
        """Return the position of ':' if the content at ``pos`` is a single line implicit mapping key."""
        src = self.src
        end = self.line_end(pos)
        char = src[pos]
        if char == "*":
            pos += 1
            while src[pos] in _ANCHOR_CHARS:
                pos += 1
        elif char in "'\"":
            pos += 1
            while pos < end:
                if char == "'" and src[pos] == "'":
                    if src[pos + 1] != "'":
                        break
                    pos += 1
                elif char == '"' and src[pos] == "\\":
                    pos += 1
                elif char == '"' and src[pos] == '"':
                    break
                pos += 1
            if pos >= end:
                return None
            pos += 1
        elif char in "[{":
            depth = 0
            quote = ""
            while pos < end:
                current = src[pos]
                if quote:
                    if current == "\\" and quote == '"':
                        pos += 1
                    elif current == quote:
                        quote = ""
                elif current in "'\"" and src[pos - 1] in " \t[{,:":
                    quote = current
                elif current in "[{":
                    depth += 1
                elif current in "]}":
                    depth -= 1
                    if depth == 0:
                        break
                elif current == "#" and src[pos - 1] in _WS:
                    return None
                pos += 1
            if pos >= end:
                return None
            pos += 1
        elif char in "|>" or char in _WS_OR_EOL:
            return None
        else:
            saved = self.pos
            self.pos = pos
            try:
                if not self.can_start_plain(flow=False):
                    return None
                while True:
                    current = src[self.pos]
                    if current in "\n\0" or (current == "#" and src[self.pos - 1] in _WS):
                        return None
                    if current == ":" and src[self.pos + 1] in _WS_OR_EOL:
                        return self.pos
                    self.pos += 1
            finally:
                self.pos = saved
        while src[pos] in _WS:
            pos += 1
        if src[pos] == ":" and src[pos + 1] in _WS_OR_EOL:
            return pos
        return None

    # ------------------------------------------------------------------ flow context

    def parse_flow_collection(self) -> Any:
        return self.parse_flow_sequence() if self.src[self.pos] == "[" else self.parse_flow_mapping()

    def parse_flow_sequence(self) -> list[Any]:
        start = self.pos
        self.pos += 1
        items: list[Any] = []
        while True:
            self.skip_blank_flow(start)
            if self.src[self.pos] == "]":
                self.pos += 1
                return items
            if items:
                if self.src[self.pos] != ",":
                    raise self.error("expected ',' or ']' in flow sequence")
                self.pos += 1
                self.skip_blank_flow(start)
                if self.src[self.pos] == "]":
                    self.pos += 1
                    return items
            entry_pos = self.pos
            explicit = self.is_indicator("?")
            if explicit:
                self.pos += 1
                self.skip_blank_flow(start)
            if self.src[self.pos] == ":":
                key = None
            else:
                key = self.parse_flow_node(start, allow_empty=explicit)
            self.skip_blank_flow(start)
            if self.src[self.pos] == ":":
                self.pos += 1
                value = self.parse_flow_value(start)
                items.append(self.build_mapping([(self.check_key(key, entry_pos), value, entry_pos)]))
            elif explicit:
                items.append(self.build_mapping([(self.check_key(key, entry_pos), None, entry_pos)]))
            else:
                items.append(key)

    def parse_flow_mapping(self) -> dict[Any, Any]:
        start = self.pos
        self.pos += 1
        entries: list[tuple[Any, Any, int]] = []
        while True:
            self.skip_blank_flow(start)
            if self.src[self.pos] == "}":
                self.pos += 1
                return self.build_mapping(entries)
            if entries:
                if self.src[self.pos] != ",":
                    raise self.error("expected ',' or '}' in flow mapping")
                self.pos += 1
                self.skip_blank_flow(start)
                if self.src[self.pos] == "}":
                    self.pos += 1
                    return self.build_mapping(entries)
            entry_pos = self.pos
            if self.is_indicator("?"):
                self.pos += 1
                self.skip_blank_flow(start)
            if self.src[self.pos] == ":":
                key = None
            else:
                key = self.parse_flow_node(start, allow_empty=True, as_key=True)
            self.skip_blank_flow(start)
            value = None
            if self.src[self.pos] == ":":
                self.pos += 1
                value = self.parse_flow_value(start)
            entries.append((self.check_key(key, entry_pos), value, entry_pos))

    def parse_flow_value(self, start: int) -> Any:
        self.skip_blank_flow(start)
        if self.src[self.pos] in ",]}":
            return None
        return self.parse_flow_node(start, allow_empty=True)

    def parse_flow_node(self, start: int, allow_empty: bool = False, as_key: bool = False) -> Any:
        self.skip_blank_flow(start)
        node_start = self.pos
        props = self.scan_properties()
        if props is not None:
            self.skip_blank_flow(start)
        char = self.src[self.pos]
        if char == "*":
            if props is not None:
                raise self.error("an alias node cannot have properties", node_start)
            return self.parse_alias()
        if char in "[{":
            return self.construct_collection(self.parse_flow_collection(), props, node_start)
        if char in "'\"":
            return self.finish_scalar(self.scan_quoted(), False, props, node_start, as_key=as_key)
        if char in ",]}:":
            if props is None and not allow_empty:
                raise self.error(f"expected a node, but found {char!r}")
            return self.construct_empty(props)
        if not self.can_start_plain(flow=True):
            raise self.error(f"found character {char!r} that cannot start any token")
        return self.finish_scalar(self.scan_plain(-1, flow=True), True, props, node_start, as_key=as_key)

    # ------------------------------------------------------------------ properties and aliases

    def scan_properties(self) -> tuple[str | None, str | None] | None:
        anchor: str | None = None
        tag: str | None = None
        start = self.pos
        while self.src[self.pos] in "&!":
            if self.src[self.pos] == "&":
                if anchor is not None:
                    raise self.error("found duplicate anchor property")
                self.pos += 1
                anchor = self.scan_anchor_name()
            else:
                if tag is not None:
                    raise self.error("found duplicate tag property")
                tag = self.scan_tag()
            self.skip_inline_ws()
        if anchor is None and tag is None:
            self.pos = start
            return None
        return anchor, tag

    def scan_anchor_name(self) -> str:
        start = self.pos
        while self.src[self.pos] in _ANCHOR_CHARS:
            self.pos += 1
        if self.pos == start or self.src[self.pos] not in " \t\n\0?:,]}%@`":
            raise self.error("expected alphabetic or numeric character in anchor or alias name")
        return self.src[start : self.pos]

    def scan_tag(self) -> str:
        start = self.pos
        if self.ch(1) == "<":
            self.pos += 2
            tag = self.scan_tag_uri()
            if self.src[self.pos] != ">":
                raise self.error("expected '>' at the end of a verbatim tag")
            self.pos += 1
        elif self.ch(1) in _WS_OR_EOL:
            self.pos += 1
            tag = "!"
        else:
            end = self.pos + 1
            while self.src[end] not in "!" + _WS_OR_EOL:
                end += 1
            if self.src[end] == "!":
                handle = self.src[self.pos : end + 1]
                if not re.fullmatch(r"!(?:[0-9A-Za-z_-]*!)?", handle):
                    raise self.error(f"invalid tag handle {handle!r}")
                self.pos = end + 1
            else:
                handle = "!"
                self.pos += 1
            if handle not in self.tag_handles:
                raise self.error(f"found undefined tag handle {handle!r}", start)
            tag = self.tag_handles[handle] + self.scan_tag_uri()
        if self.src[self.pos] not in _WS_OR_EOL:
            raise self.error(f"expected ' ' after a tag, but found {self.src[self.pos]!r}")
        return tag

    def scan_tag_uri(self) -> str:
        start = self.pos
        while self.src[self.pos] in _TAG_URI_CHARS:
            self.pos += 1
        if self.pos == start:
            raise self.error("expected a tag URI")
        try:
            return unquote(self.src[start : self.pos], errors="strict")
        except UnicodeDecodeError as err:
            raise self.error("invalid URI escape sequence in tag", start) from err

    def parse_alias(self) -> Any:
        start = self.pos
        self.pos += 1
        name = self.scan_anchor_name()
        if name not in self.anchors:
            raise self.error(f"found undefined alias {name!r}", start)
        return self.anchors[name]

    # ------------------------------------------------------------------ scalars

    def can_start_plain(self, flow: bool) -> bool:
        char = self.src[self.pos]
        if char not in _PLAIN_START_INDICATORS:
            return True
        return self.ch(1) not in _WS_OR_EOL and (char == "-" or (not flow and char in "?:"))

    def scan_plain(self, indent: int, flow: bool) -> str:
        """Scan a (possibly multi-line) plain scalar. Continuation lines must be indented more than ``indent``."""
        src = self.src
        chunks: list[str] = []
        pending = ""
        end = self.pos
        while True:
            if src[self.pos] == "#":
                break
            chunk_start = self.pos
            while True:
                char = src[self.pos]
                if char in _WS_OR_EOL:
                    break
                if char == ":" and (
                    src[self.pos + 1] in _WS_OR_EOL or (flow and src[self.pos + 1] in _FLOW_INDICATORS)
                ):
                    break
                if flow and char in _FLOW_INDICATORS:
                    break
                self.pos += 1
            if self.pos == chunk_start:
                break
            chunks.append(pending)
            chunks.append(src[chunk_start : self.pos])
            end = self.pos

            whitespace_start = self.pos
            while src[self.pos] in _WS:
                self.pos += 1
            if src[self.pos] != "\n":
                if self.pos == whitespace_start:
                    break
                pending = src[whitespace_start : self.pos]
                continue
            breaks = 0
            stop = False
            while src[self.pos] == "\n":
                self.pos += 1
                if self.is_document_marker():
                    stop = True
                    break
                while src[self.pos] == " " or (src[self.pos] == "\t" and (flow or self.is_blank_rest())):
                    self.pos += 1
                if src[self.pos] == "\n":
                    breaks += 1
            if stop or (not flow and self.column() <= indent):
                break
            pending = "\n" * breaks if breaks else " "
        self.pos = end
        return "".join(chunks)

    def is_blank_rest(self) -> bool:
        """True if the rest of the current line contains only white space."""
        return self.src[self.pos : self.line_end(self.pos)].strip(_WS) == ""

    def scan_quoted(self) -> str:
        src = self.src
        start = self.pos
        double = src[self.pos] == '"'
        self.pos += 1
        chunks: list[str] = []
        while True:
            run_start = self.pos
            while src[self.pos] not in "'\"\\ \t\n\0":
                self.pos += 1
            chunks.append(src[run_start : self.pos])
            char = src[self.pos]
            if char == "'":
                if double:
                    chunks.append("'")
                    self.pos += 1
                elif src[self.pos + 1] == "'":
                    chunks.append("'")
                    self.pos += 2
                else:
                    self.pos += 1
                    return "".join(chunks)
            elif char == '"':
                self.pos += 1
                if double:
                    return "".join(chunks)
                chunks.append('"')
            elif char == "\\":
                self.pos += 1
                if double:
                    chunks.append(self.scan_escape(start))
                else:
                    chunks.append("\\")
            elif char == "\0":
                raise self.error("found unexpected end of stream while scanning a quoted scalar", start)
            else:
                whitespace_start = self.pos
                while src[self.pos] in _WS:
                    self.pos += 1
                if src[self.pos] == "\n":
                    self.pos += 1
                    breaks = self.scan_quoted_breaks(start)
                    chunks.append("\n" * breaks if breaks else " ")
                elif src[self.pos] != "\0":
                    chunks.append(src[whitespace_start : self.pos])

    def scan_quoted_breaks(self, start: int) -> int:
        breaks = 0
        while True:
            if self.is_document_marker():
                raise self.error("found unexpected document separator while scanning a quoted scalar", start)
            while self.src[self.pos] in _WS:
                self.pos += 1
            if self.src[self.pos] != "\n":
                return breaks
            breaks += 1
            self.pos += 1

    def scan_escape(self, start: int) -> str:
        char = self.src[self.pos]
        if char in _ESCAPES:
            self.pos += 1
            return _ESCAPES[char]
        if char in _ESCAPE_CODES:
            length = _ESCAPE_CODES[char]
            digits = self.src[self.pos + 1 : self.pos + 1 + length]
            if len(digits) != length or not all(d in _HEX_DIGITS for d in digits):
                raise self.error(f"expected escape sequence of {length} hexadecimal numbers")
            code = int(digits, 16)
            if code > 0x10FFFF:
                raise self.error(f"invalid Unicode code point \\{char}{digits}")
            self.pos += 1 + length
            return chr(code)
        if char == "\n":
            self.pos += 1
            return "\n" * self.scan_quoted_breaks(start)
        raise self.error(f"found unknown escape character {char!r}")

    def scan_block_scalar(self, indent: int) -> str:
        src = self.src
        folded = src[self.pos] == ">"
        self.pos += 1
        chomping: bool | None = None
        increment: int | None = None
        for _ in range(2):
            char = src[self.pos]
            if char in "+-" and chomping is None:
                chomping = char == "+"
                self.pos += 1
            elif char in "0123456789" and increment is None:
                if char == "0":
                    raise self.error("expected indentation indicator in the range 1-9, but found 0")
                increment = int(char)
                self.pos += 1
        if src[self.pos] not in _WS_OR_EOL:
            raise self.error(f"expected chomping or indentation indicators, but found {src[self.pos]!r}")
        self.skip_inline_ws()
        if src[self.pos] == "#":
            self.pos = self.line_end(self.pos)
        if src[self.pos] not in "\n\0":
            raise self.error(f"expected a comment or a line break, but found {src[self.pos]!r}")
        if src[self.pos] == "\n":
            self.pos += 1

        min_indent = max(indent + 1, 1)
        if increment is None:
            breaks = 0
            max_indent = 0
            while src[self.pos] in " \n":
                if src[self.pos] == " ":
                    self.pos += 1
                    max_indent = max(max_indent, self.column())
                else:
                    self.pos += 1
                    breaks += 1
            block_indent = max(min_indent, max_indent)
        else:
            block_indent = min_indent + increment - 1
            breaks = self.scan_block_breaks(block_indent)

        chunks: list[str] = []
        line_break = ""
        while self.column() == block_indent and src[self.pos] != "\0":
            chunks.append("\n" * breaks)
            leading_non_space = src[self.pos] not in _WS
            end = self.line_end(self.pos)
            chunks.append(src[self.pos : end])
            self.pos = end
            line_break = "\n" if src[self.pos] == "\n" else ""
            self.pos += len(line_break)
            breaks = self.scan_block_breaks(block_indent)
            if self.column() != block_indent or src[self.pos] == "\0":
                break
            if folded and line_break == "\n" and leading_non_space and src[self.pos] not in _WS:
                if not breaks:
                    chunks.append(" ")
            else:
                chunks.append(line_break)
        if chomping is not False:
            chunks.append(line_break)
        if chomping is True:
            chunks.append("\n" * breaks)
        if src[self.pos] != "\0":
            self.pos = self.line_start(self.pos)
        return "".join(chunks)

    def scan_block_breaks(self, block_indent: int) -> int:
        breaks = 0
        while self.column() < block_indent and self.src[self.pos] == " ":
            self.pos += 1
        while self.src[self.pos] == "\n":
            breaks += 1
            self.pos += 1
            while self.column() < block_indent and self.src[self.pos] == " ":
                self.pos += 1
        return breaks

    # ------------------------------------------------------------------ construction

    def register_anchor(self, props: tuple | None, value: Any, pos: int) -> Any:
        if props is not None and props[0] is not None:
            if props[0] in self.anchors:
                raise self.error(f"found duplicate anchor {props[0]!r}", pos)
            self.anchors[props[0]] = value
        return value

    def construct_empty(self, props: tuple | None) -> Any:
        return self.finish_scalar("", True, props, self.pos)

    def finish_scalar(self, text: str, plain: bool, props: tuple | None, pos: int, as_key: bool = False) -> Any:
        tag = props[1] if props is not None else None
        if tag is None or tag == "!":
            tag = _resolve(text) if plain or tag == "!" else _STR
        try:
            value = self.construct_scalar(text, tag, as_key)
        except (ValueError, KeyError, binascii.Error) as err:
            raise self.error(f"cannot construct {tag!r} from {text!r}", pos) from err
        return self.register_anchor(props, value, pos)

    def construct_scalar(self, text: str, tag: str, as_key: bool) -> Any:
        if tag == _STR:
            return text
        if tag == _NULL:
            return None
        if tag == _BOOL:
            return _BOOL_VALUES[text.lower()]
        if tag == _INT:
            return _construct_int(text)
        if tag == _FLOAT:
            return _construct_float(text)
        if tag == _TIMESTAMP:
            return _construct_timestamp(text)
        if tag == _BINARY:
            return base64.decodebytes(text.encode("ascii"))
        if tag == _MERGE:
            return _MERGE_KEY if as_key else text
        if tag in (_SEQ, _MAP, _SET, _OMAP, _PAIRS):
            raise ValueError(f"expected a collection for tag {tag!r}, but found a scalar")
        raise ValueError(f"could not determine a constructor for the tag {tag!r}")

    def construct_collection(self, value: Any, props: tuple | None, pos: int) -> Any:
        tag = props[1] if props is not None else None
        if isinstance(value, list):
            if tag in (_OMAP, _PAIRS):
                pairs = []
                for item in value:
                    if not isinstance(item, dict) or len(item) != 1:
                        raise self.error(f"expected a single-pair mapping in {tag!r}", pos)
                    pairs.extend(item.items())
                value = pairs
            elif tag not in (None, "!", _SEQ):
                raise self.error(f"cannot construct {tag!r} from a sequence", pos)
        elif tag == _SET:
            value = set(value)
        elif tag not in (None, "!", _MAP):
            raise self.error(f"cannot construct {tag!r} from a mapping", pos)
        return self.register_anchor(props, value, pos)

    def check_key(self, key: Any, pos: int) -> Any:
        if key is _MERGE_KEY:
            return key
        try:
            hash(key)
        except TypeError:
            raise self.error("found unhashable key", pos) from None
        return key

    def build_mapping(self, entries: list[tuple[Any, Any, int]]) -> dict[Any, Any]:
        """Build a dict from (key, value, pos) entries resolving merge keys like PyYAML."""
        merged: list[tuple[Any, Any]] = []
        explicit: list[tuple[Any, Any]] = []
        for key, value, pos in entries:
            if key is not _MERGE_KEY:
                explicit.append((key, value))
            elif isinstance(value, dict):
                merged.extend(value.items())
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
                for item in reversed(value):
                    merged.extend(item.items())
            else:
                raise self.error("expected a mapping or a list of mappings for merging", pos)
        return dict(merged + explicit)
