from abc import abstractmethod
from collections import OrderedDict
from typing import List, Dict, Callable, Type

from pydantic import BaseSettings

from confme.utils.base_exception import ConfmeException


class NodeGenerator:

    @abstractmethod
    def is_applicable(self, node: Dict, definitions: Dict): pass

    @abstractmethod
    def generate(self, node: Dict, definitions: Dict, traverse: Callable): pass


class PrimitiveNodeGenerator(NodeGenerator):
    PRIMITIVE_TYPES = {
        'string': 'bla',
        'integer': 42,
        'number': 42.42
    }

    def is_applicable(self, node: Dict, definitions: Dict):
        if 'type' in node and node['type'] \
                in self.PRIMITIVE_TYPES.keys():
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        return self.PRIMITIVE_TYPES[node['type']]


class EnumNodeGenerator(NodeGenerator):

    def is_applicable(self, node: Dict, definitions: Dict):
        if 'enum' in node:
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        return node['enum'][0]


class ObjectNodeGenerator(NodeGenerator):
    def is_applicable(self, node: Dict, definitions: Dict):
        if 'type' in node and node['type'] == 'object' and 'properties' in node:
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        res = OrderedDict()
        for k, p in node['properties'].items():
            res[k] = traverse(p)
        return res


class DictNodeGenerator(NodeGenerator):
    def is_applicable(self, node: Dict, definitions: Dict):
        if 'type' in node and node['type'] == 'object' and 'additionalProperties' in node:
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        value = traverse(node['additionalProperties'])
        return OrderedDict(**{'value1': value, 'value2': value})


class ListNodeGenerator(NodeGenerator):
    def is_applicable(self, node: Dict, definitions: Dict):
        if 'type' in node and node['type'] == 'array':
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        element = traverse(node['items'])
        return [element] * 3


class AllOffNodeGenerator(NodeGenerator):

    def is_applicable(self, node: Dict, definitions: Dict):
        if 'allOf' in node:
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        return traverse(node['allOf'][0])


class AnyOffNodeGenerator(NodeGenerator):

    def is_applicable(self, node: Dict, definitions: Dict):
        if 'anyOf' in node:
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        return traverse(node['anyOf'][0])


class RefNodeGenerator(NodeGenerator):
    def is_applicable(self, node: Dict, definitions: Dict):
        if '$ref' in node:
            return True
        return False

    def generate(self, node: Dict, definitions: Dict, traverse: Callable):
        ref = node['$ref'].split('/')[-1]
        definition = definitions[ref]
        return traverse(definition)


class Generator:

    def __init__(self, generators: List[NodeGenerator] = None):
        if generators is None:
            generators = [RefNodeGenerator(),
                          AllOffNodeGenerator(),
                          ListNodeGenerator(),
                          ObjectNodeGenerator(),
                          DictNodeGenerator(),
                          PrimitiveNodeGenerator(),
                          EnumNodeGenerator()]

        self._generators = generators
        self._definitions = {}

    def generate(self, config: Type[BaseSettings]) -> Dict:
        return self._traverse(config.schema())

    def _traverse(self, node: Dict):
        self._extract_definitions(node)
        for g in self._generators:
            if g.is_applicable(node, self._definitions):
                return g.generate(node, self._definitions, self._traverse)

        raise ConfmeException(f'Could not find Generator to handle node: {node}')

    def _extract_definitions(self, node: Dict):
        if 'definitions' in node:
            self._definitions.update(**node['definitions'])
