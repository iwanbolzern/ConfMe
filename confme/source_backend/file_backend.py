"""base module for all file backends e.g. yaml, json, xml, ..."""
import logging
from io import StringIO
from abc import abstractmethod
from os import path
from typing import Dict, List

import yaml
from yaml.parser import ParserError


class BaseFileParser:
    """Base class for all file backends"""

    @abstractmethod
    def get_endings(self) -> List[str]:
        """Returns a list of file endings (including point e.g. .json)
        supported by the given backend
        :return: List of supported file endings
        """
        pass

    @abstractmethod
    def parse(self, file: StringIO) -> Dict:
        """Base method for converting the given string into a python dict
        :param file: StringIO with access to the raw file data
        :return: Dict of file content
        """
        pass


class YamlFileParser(BaseFileParser):
    """File Parser for yaml files"""

    def get_endings(self) -> List[str]:
        """Returns all yaml file endins
        :return: List of yaml file endings
        """
        return ['.yaml', '.yml']

    def parse(self, file: StringIO) -> Dict:
        """Converts the given yaml file into a python dict
        :param file: yaml file stream
        :return: Content of yaml file converted to dict
        """
        try:
            return yaml.safe_load(file)
        except ParserError:
            logging.exception('Not able to parse yaml file')
            raise ParserError


FILE_PARSER = [
    YamlFileParser()
]


def parse_file(file_path: str) -> Dict:
    """Parses the given file with the right file parser based on the filename ending of the
    given file_path
    :param file_path: path to the file
    :return: Dict with content of the file
    """
    ending = path.splitext(file_path)[-1]
    applicable_file_parsers = [p for p in FILE_PARSER if ending in p.get_endings()]
    if len(applicable_file_parsers) < 0:
        raise Exception(f'File Ending {ending} not known')
    if len(applicable_file_parsers) > 1:
        raise Exception(f'More than one parser registered for this file ending... 🧐')

    with open(file_path, 'r') as file:
        return applicable_file_parsers[0].parse(file)
