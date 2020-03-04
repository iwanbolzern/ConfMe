from typing import Any

from confme.parsing.parser_base import Parser, ParseError, CustomType


class Range(CustomType):
    def __class_getitem__(cls, params):
        assert len(params) == 3, 'Params must be of length two'
        assert params[0] in [int, float], 'Type must be numeric (int, float)'
        assert type(params[1]) in [int, float], 'Lower limit must be of type int or float)'
        assert type(params[2]) in [int, float], 'Upper limit must be of type int or float)'

        cls.__value_type__ = params[0]
        cls.__from__ = params[1]
        cls.__to__ = params[2]

        return cls


class ParserRange(Parser):

    def __init__(self, propagate_parse_cb):
        super(ParserRange, self).__init__(propagate_parse_cb)

    def is_applicable(self, attr_name: str, attr_type: Any):
        return attr_type == Range

    def parse(self, attr_name: str, attr_type: Range, value: Any):
        if not isinstance(value, attr_type.__value_type__):
            raise ParseError(f'Value not of specified type: {attr_type.__value_type__}')

        if not (attr_type.__from__ <= value <= attr_type.__to__):
            raise ParseError(f'Value {value} must be in between {attr_type.__from__} and {attr_type.__to__}')

        return self.propagate_parse_cb(attr_name,
                                       attr_type.__value_type__,
                                       value)
