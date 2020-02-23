from typing import Union

from confme.parsing.parser_base import Parser, ParseError


class ParserPrimitive(Parser):
    SCALAR_TYPES = Union[int, float, str]

    def __init__(self, propagate_parse_cb):
        super(ParserPrimitive, self).__init__(propagate_parse_cb)

    def is_applicable(self, attr_name, attr_type):
        return self._check_union(attr_type, self.SCALAR_TYPES)

    def parse(self, attr_name, attr_type, value):
        try:
            return attr_type(value)
        except ValueError:
            raise ParseError()
