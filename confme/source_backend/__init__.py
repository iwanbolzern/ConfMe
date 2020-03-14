from os import path
from typing import Dict

from confme.source_backend.backend_yaml import YamlFileParser

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
