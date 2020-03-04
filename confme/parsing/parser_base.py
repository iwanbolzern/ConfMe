from abc import abstractmethod, ABC


class ParseError(Exception):

    def __init__(self, msg: str=None):
        self.msg = msg


class Parser(ABC):

    def __init__(self, propagate_parse_cb):
        self.propagate_parse_cb = propagate_parse_cb

    @abstractmethod
    def is_applicable(self, attr_name, attr_type):
        pass

    def _check_union(self, type_to_check, union):
        return any([union_t == type_to_check for union_t in union.__args__])

    def parse(self, attr_name, attr_type, value):
        pass


class CustomType(ABC):
    __slots__ = ()

    def __new__(cls, *args, **kwds):
        raise SyntaxError(f'{cls.__name__} is only a marker class and can not be instantiated')

    def __init_subclass__(cls, *args, **kwargs):
        pass