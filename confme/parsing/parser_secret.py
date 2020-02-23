import os
from typing import Any

from confme.parsing.parser_base import Parser, ParseError


class Secret:
    __slots__ = ()

    def __new__(cls, *args, **kwds):
        raise SyntaxError(f'{cls.__name__} is only a marker class and can not be instantiated')

    def __class_getitem__(cls, params):
        assert len(params) == 2, 'Params must be of length two'

        cls.__key__ = params[0]
        cls.__value_type__ = params[1]

        return cls

    def __init_subclass__(cls, *args, **kwargs):
        pass


class ParserSecret(Parser):

    def __init__(self, propagate_parse_cb):
        super(ParserSecret, self).__init__(propagate_parse_cb)

    def is_applicable(self, attr_name: str, attr_type: Any):
        return attr_type == Secret

    def parse(self, attr_name: str, attr_type: Secret, value: Any):
        if attr_type.__key__ not in os.environ:
            raise ParseError(f'Secret with name {attr_type.__key__} not found')

        return self.propagate_parse_cb(attr_name,
                                       attr_type.__value_type__,
                                       os.environ[attr_type.__key__])

