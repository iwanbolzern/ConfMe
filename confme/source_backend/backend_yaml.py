"""module for parsing yaml files"""

import logging
from typing import Any, TextIO

import yaml
from yaml.parser import ParserError

from confme.source_backend.backend_base import BaseFileParser


class YamlFileParser(BaseFileParser):
    """File Parser for yaml files"""

    def get_endings(self) -> list[str]:
        """Returns all yaml file endings
        :return: List of yaml file endings
        """
        return [".yaml", ".yml"]

    def parse(self, file: TextIO) -> dict[str, Any]:
        """Converts the given yaml file into a python dict
        :param file: yaml file stream
        :return: Content of yaml file converted to dict
        """
        try:
            return yaml.safe_load(file)
        except ParserError as err:
            logging.exception("Not able to parse yaml file")
            raise ParserError from err
