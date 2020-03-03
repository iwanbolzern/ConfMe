from typing import Any

from confme.parsing.parser_secret import ParserSecret
from confme.parsing.parser_primitive import ParserPrimitive


class UnknownTypeException(Exception):
    pass


def parse(attr_name: str, attr_type: Any, value: Any):
    parser = [p for p in PARSER if p.is_applicable(attr_name, attr_type)]
    if len(parser) > 1:
        raise Exception('More than one Parser present to parse the same attribute type')
    if len(parser) < 1:
        raise UnknownTypeException()

    return parser[0].parse(attr_name, attr_type, value)


PARSER = [
    ParserPrimitive(parse),
    ParserSecret(parse)
]
