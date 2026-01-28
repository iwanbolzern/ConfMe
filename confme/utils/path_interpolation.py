import re
from pathlib import Path
from typing import Any


def interpolate_paths(config: dict[str, Any], config_dir: Path) -> dict[str, Any]:
    """Recursively interpolate path placeholders in the configuration dictionary.

    Supports the following placeholders:
    - %(here)s: Replaced with the absolute path to the directory containing the config file

    :param config: Configuration dictionary to process
    :param config_dir: Absolute path to the directory containing the configuration file
    :return: Configuration dictionary with interpolated paths
    """
    return _recursive_interpolate(config, config_dir)


def _recursive_interpolate(obj: Any, config_dir: Path) -> Any:
    """Recursively process configuration values and interpolate path placeholders.

    :param obj: Any configuration value (dict, list, str, or other)
    :param config_dir: Absolute path to the directory containing the configuration file
    :return: Processed value with interpolated paths
    """
    if isinstance(obj, dict):
        return {key: _recursive_interpolate(value, config_dir) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_recursive_interpolate(item, config_dir) for item in obj]
    elif isinstance(obj, str):
        return _interpolate_string(obj, config_dir)
    else:
        return obj


def _interpolate_string(value: str, config_dir: Path) -> str:
    """Interpolate path placeholders in a string value.

    :param value: String value that may contain placeholders
    :param config_dir: Absolute path to the directory containing the configuration file
    :return: String with placeholders replaced
    """
    # Define available placeholders
    placeholders = {
        "here": str(config_dir.resolve()),
    }

    # Replace %(name)s style placeholders
    pattern = re.compile(r"%\((\w+)\)s")

    def replace_match(match: re.Match[str]) -> str:
        placeholder_name = match.group(1)
        if placeholder_name in placeholders:
            return placeholders[placeholder_name]
        # If placeholder is not recognized, leave it unchanged
        return match.group(0)

    return pattern.sub(replace_match, value)
