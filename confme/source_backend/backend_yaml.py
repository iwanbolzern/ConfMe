"""module for parsing yaml files"""
import logging
from io import StringIO
from typing import Dict, List

import yaml
from yaml.parser import ParserError

from confme.source_backend.backend_base import BaseFileParser


class YamlFileParser(BaseFileParser):
    """File Parser for yaml files"""

    def get_endings(self) -> List[str]:
        """Returns all yaml file endings
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
