"""Tests for path interpolation functionality."""

import uuid
from pathlib import Path

import pytest

from confme import BaseConfig
from confme.utils.path_interpolation import _interpolate_string, interpolate_paths


class PathConfig(BaseConfig):
    """Config model for testing path interpolation."""

    script_location: str
    data_dir: str
    simple_value: int


class NestedPathConfig(BaseConfig):
    """Config model for testing nested path interpolation."""

    name: str
    paths: "PathsConfig"


class PathsConfig(BaseConfig):
    """Nested config with paths."""

    scripts: str
    data: str
    logs: str


@pytest.fixture
def config_with_paths_yaml(tmp_path: Path):
    """Create a config file with %(here)s placeholders."""
    config_content = 'script_location: "%(here)s/scripts"\ndata_dir: "%(here)s/data"\nsimple_value: 42\n'

    config_path = tmp_path / f"{uuid.uuid4()}.yaml"
    config_path.write_text(config_content)

    return config_path


@pytest.fixture
def nested_config_yaml(tmp_path: Path):
    """Create a nested config file with %(here)s placeholders."""
    config_content = (
        'name: "my_app"\npaths:\n  scripts: "%(here)s/scripts"\n  data: "%(here)s/data"\n  logs: "%(here)s/logs"\n'
    )

    config_path = tmp_path / f"{uuid.uuid4()}.yaml"
    config_path.write_text(config_content)

    return config_path


# Tests for _interpolate_string function


def test_interpolate_here_placeholder(tmp_path: Path):
    """Test that %(here)s is replaced with config directory."""
    result = _interpolate_string("%(here)s/scripts", tmp_path)
    assert result == f"{tmp_path.resolve()}/scripts"


def test_interpolate_multiple_placeholders(tmp_path: Path):
    """Test multiple %(here)s placeholders in same string."""
    result = _interpolate_string("%(here)s/scripts:%(here)s/data", tmp_path)
    expected = f"{tmp_path.resolve()}/scripts:{tmp_path.resolve()}/data"
    assert result == expected


def test_no_placeholder(tmp_path: Path):
    """Test string without placeholder remains unchanged."""
    result = _interpolate_string("/absolute/path/to/scripts", tmp_path)
    assert result == "/absolute/path/to/scripts"


def test_unknown_placeholder_unchanged(tmp_path: Path):
    """Test unknown placeholders are left unchanged."""
    result = _interpolate_string("%(unknown)s/scripts", tmp_path)
    assert result == "%(unknown)s/scripts"


# Tests for interpolate_paths function


def test_interpolate_simple_dict(tmp_path: Path):
    """Test interpolation in a simple dictionary."""
    config = {
        "path": "%(here)s/scripts",
        "name": "test",
        "count": 42,
    }
    result = interpolate_paths(config, tmp_path)

    assert result["path"] == f"{tmp_path.resolve()}/scripts"
    assert result["name"] == "test"
    assert result["count"] == 42


def test_interpolate_nested_dict(tmp_path: Path):
    """Test interpolation in nested dictionaries."""
    config = {
        "level1": {
            "path": "%(here)s/data",
            "level2": {
                "another_path": "%(here)s/nested",
            },
        }
    }
    result = interpolate_paths(config, tmp_path)

    assert result["level1"]["path"] == f"{tmp_path.resolve()}/data"
    assert result["level1"]["level2"]["another_path"] == f"{tmp_path.resolve()}/nested"


def test_interpolate_list_values(tmp_path: Path):
    """Test interpolation in list values."""
    config = {
        "paths": [
            "%(here)s/first",
            "%(here)s/second",
            "/absolute/path",
        ]
    }
    result = interpolate_paths(config, tmp_path)

    assert result["paths"][0] == f"{tmp_path.resolve()}/first"
    assert result["paths"][1] == f"{tmp_path.resolve()}/second"
    assert result["paths"][2] == "/absolute/path"


def test_interpolate_mixed_types(tmp_path: Path):
    """Test that non-string types are preserved."""
    config = {
        "path": "%(here)s/scripts",
        "count": 42,
        "enabled": True,
        "ratio": 3.14,
        "nothing": None,
    }
    result = interpolate_paths(config, tmp_path)

    assert result["path"] == f"{tmp_path.resolve()}/scripts"
    assert result["count"] == 42
    assert result["enabled"] is True
    assert result["ratio"] == 3.14
    assert result["nothing"] is None


# Integration tests for loading config with path interpolation


def test_load_config_with_here_placeholder(config_with_paths_yaml: Path):
    """Test loading a config file with %(here)s placeholders."""
    config = PathConfig.load(config_with_paths_yaml)
    config_dir = config_with_paths_yaml.parent.resolve()

    assert config.script_location == f"{config_dir}/scripts"
    assert config.data_dir == f"{config_dir}/data"
    assert config.simple_value == 42


def test_load_nested_config_with_here_placeholder(nested_config_yaml: Path):
    """Test loading a nested config with %(here)s placeholders."""
    config = NestedPathConfig.load(nested_config_yaml)
    config_dir = nested_config_yaml.parent.resolve()

    assert config.name == "my_app"
    assert config.paths.scripts == f"{config_dir}/scripts"
    assert config.paths.data == f"{config_dir}/data"
    assert config.paths.logs == f"{config_dir}/logs"


def test_paths_resolve_correctly_from_subdirectory(tmp_path: Path):
    """Test that %(here)s resolves correctly when config is in a subdirectory."""
    # Create a subdirectory for the config file
    config_subdir = tmp_path / "config" / "nested"
    config_subdir.mkdir(parents=True)

    config_content = 'script_location: "%(here)s/scripts"\ndata_dir: "%(here)s/data"\nsimple_value: 1\n'
    config_path = config_subdir / "app.yaml"
    config_path.write_text(config_content)

    config = PathConfig.load(config_path)

    assert config.script_location == f"{config_subdir.resolve()}/scripts"
    assert config.data_dir == f"{config_subdir.resolve()}/data"


def test_relative_path_to_config_file(tmp_path: Path, monkeypatch):
    """Test that %(here)s works when config path is given as relative path."""
    # Create config in tmp_path
    config_content = 'script_location: "%(here)s/scripts"\ndata_dir: "%(here)s/data"\nsimple_value: 1\n'
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_content)

    # Change to tmp_path and load with relative path
    monkeypatch.chdir(tmp_path)
    config = PathConfig.load("test_config.yaml")

    assert config.script_location == f"{tmp_path.resolve()}/scripts"
    assert config.data_dir == f"{tmp_path.resolve()}/data"
