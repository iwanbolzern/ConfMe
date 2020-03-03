
import logging
from abc import abstractmethod
from os import path
from typing import Dict

import yaml
from yaml.parser import ParserError


class BaseFileParser:
    @abstractmethod
    def get_endings(self):
        pass

    @abstractmethod
    def parse(self, file: str):
        pass


class YamlFileParser(BaseFileParser):

    def get_endings(self):
        return ['.yaml', '.yml']

    def parse(self, file):
        try:
            return yaml.safe_load(file)
        except ParserError:
            logging.exception('Not able to parse yaml file')
            raise ParserError


FILE_PARSER = [
    YamlFileParser()
]


def parse_file(file_path: str) -> Dict:
    ending = path.splitext(file_path)[-1]
    applicable_file_parsers = [p for p in FILE_PARSER if ending in p.get_endings()]
    if len(applicable_file_parsers) < 0:
        raise Exception(f'File Ending {ending} not known')
    if len(applicable_file_parsers) > 1:
        raise Exception(f'More than one parser registered for this file ending... 🧐')

    with open(file_path, 'r') as file:
        return applicable_file_parsers[0].parse(file)
