"""module for parsing yaml files"""

import logging
from typing import Any, TextIO

from confme.source_backend.backend_base import BaseFileParser
from confme.source_backend.yaml_parser import ParserError, load

__all__ = ["ParserError", "YamlFileParser"]


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
        name = getattr(file, "name", None)
        try:
            content = load(file.read(), name if isinstance(name, str) else None)
            if content is None:
                return {}
            if not isinstance(content, dict):
                raise ParserError(f"The top-level element of a configuration file must be a mapping ({name})")
            return content
        except ParserError:
            logging.exception("Not able to parse yaml file")
            raise
