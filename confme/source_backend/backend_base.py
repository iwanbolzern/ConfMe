"""base module for all file backends e.g. yaml, json, xml, ..."""
from abc import abstractmethod
from io import StringIO
from typing import Dict, List


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
