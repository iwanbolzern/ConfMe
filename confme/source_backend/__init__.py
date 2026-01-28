from os import path
from pathlib import Path
from typing import Any

from confme.source_backend.backend_yaml import YamlFileParser
from confme.utils.path_interpolation import interpolate_paths

FILE_PARSER = [YamlFileParser()]


def parse_file(file_path: str | Path, interpolate: bool = True) -> dict[str, Any]:
    """Parses the given file with the right file parser based on the filename ending of the
    given file_path. Supports path interpolation with %(here)s placeholder.

    :param file_path: path to the file
    :param interpolate: If True, interpolate path placeholders like %(here)s. Defaults to True.
    :return: Dict with content of the file
    """
    file_path_obj = Path(file_path)
    file_path_str = str(file_path_obj)
    ending = path.splitext(file_path_str)[-1]
    applicable_file_parsers = [p for p in FILE_PARSER if ending in p.get_endings()]
    if len(applicable_file_parsers) < 0:
        raise Exception(f"File Ending {ending} not known")
    if len(applicable_file_parsers) > 1:
        raise Exception("More than one parser registered for this file ending... 🧐")

    with open(file_path_str) as file:
        config = applicable_file_parsers[0].parse(file)

    if interpolate:
        config_dir = file_path_obj.parent
        config = interpolate_paths(config, config_dir)

    return config
