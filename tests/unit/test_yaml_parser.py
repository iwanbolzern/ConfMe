import datetime
import io
import math

import pytest

from confme.source_backend.backend_yaml import ParserError, YamlFileParser
from confme.source_backend.yaml_parser import load


def parse_yaml_str(content: str) -> dict:
    return YamlFileParser().parse(io.StringIO(content))


def test_parse_empty_and_comments():
    assert parse_yaml_str("") == {}
    assert parse_yaml_str("   \n# full line comment\n  # indented comment\n") == {}
    assert parse_yaml_str("---\na: 1\n...\n") == {"a": 1}


def test_parse_scalar_types():
    yaml_text = """
    int_val: 42
    neg_int: -17
    hex_val: 0x1A
    octal_val: 0755
    binary_val: 0b101
    sexagesimal: 1:30
    float_val: 42.42
    sci_float: 1.5e-3
    exp_without_dot: 1e3
    inf_val: .inf
    neg_inf: -.inf
    nan_val: .nan
    bool_true: true
    bool_yes: Yes
    bool_false: false
    bool_no: OFF
    null_val: null
    tilde_null: ~
    empty_null:
    date_val: 2024-01-31
    datetime_val: 2001-12-14t21:59:43.10-05:00
    unquoted_str: hello_world
    url_str: http://localhost:8080/api
    double_quoted: "line1\\nline2\\t\\"quoted\\" # not a comment"
    single_quoted: 'it''s a # literal string'
    """
    result = parse_yaml_str(yaml_text)
    assert result["int_val"] == 42
    assert result["neg_int"] == -17
    assert result["hex_val"] == 26
    assert result["octal_val"] == 493
    assert result["binary_val"] == 5
    assert result["sexagesimal"] == 90
    assert result["float_val"] == 42.42
    assert result["sci_float"] == 0.0015
    assert result["exp_without_dot"] == "1e3"
    assert math.isinf(result["inf_val"]) and result["inf_val"] > 0
    assert math.isinf(result["neg_inf"]) and result["neg_inf"] < 0
    assert math.isnan(result["nan_val"])
    assert result["bool_true"] is True
    assert result["bool_yes"] is True
    assert result["bool_false"] is False
    assert result["bool_no"] is False
    assert result["null_val"] is None
    assert result["tilde_null"] is None
    assert result["empty_null"] is None
    assert result["date_val"] == datetime.date(2024, 1, 31)
    assert result["datetime_val"] == datetime.datetime(
        2001, 12, 14, 21, 59, 43, 100000, tzinfo=datetime.timezone(datetime.timedelta(hours=-5))
    )
    assert result["unquoted_str"] == "hello_world"
    assert result["url_str"] == "http://localhost:8080/api"
    assert result["double_quoted"] == 'line1\nline2\t"quoted" # not a comment'
    assert result["single_quoted"] == "it's a # literal string"


def test_keys_are_resolved_like_values():
    assert load("on: 1\n2: a\n0x10: b\nnull: c\n") == {True: 1, 2: "a", 16: "b", None: "c"}


def test_apostrophes_and_quotes_in_plain_scalars():
    yaml_text = """
    message: don't panic
    name: O'Brien
    size: 5"
    mixed: it's 'quoted' "text"
    script: |
      echo "It's working" # part of the script
    """
    assert parse_yaml_str(yaml_text) == {
        "message": "don't panic",
        "name": "O'Brien",
        "size": '5"',
        "mixed": "it's 'quoted' \"text\"",
        "script": 'echo "It\'s working" # part of the script\n',
    }


def test_parse_nested_mappings_and_sequences():
    yaml_text = """
    app:
      name: "ConfMe"
      tags:
        - config
        - python
      compact_tags:
      - yaml
      - pydantic
      servers:
        - host: localhost
          port: 8000
          roles:
            - api
            - worker
        - host: 127.0.0.1
          port: 8001
          roles: []
      nested_lists:
        - - 1
          - 2
        - - 3
          - 4
    """
    result = parse_yaml_str(yaml_text)
    assert result == {
        "app": {
            "name": "ConfMe",
            "tags": ["config", "python"],
            "compact_tags": ["yaml", "pydantic"],
            "servers": [
                {"host": "localhost", "port": 8000, "roles": ["api", "worker"]},
                {"host": "127.0.0.1", "port": 8001, "roles": []},
            ],
            "nested_lists": [[1, 2], [3, 4]],
        }
    }


def test_parse_flow_collections():
    yaml_text = """
    inline_list: [1, "two", true, [3, 4]]
    inline_dict: {host: "localhost", port: 5432, nested: {a: 1}}
    json_style: {"key":"value", "list":[1,2]}
    multiline_list: [
      "alpha",
      "beta",  # comment
      "gamma",
    ]
    """
    result = parse_yaml_str(yaml_text)
    assert result == {
        "inline_list": [1, "two", True, [3, 4]],
        "inline_dict": {"host": "localhost", "port": 5432, "nested": {"a": 1}},
        "json_style": {"key": "value", "list": [1, 2]},
        "multiline_list": ["alpha", "beta", "gamma"],
    }


def test_parse_json_document():
    assert parse_yaml_str('{\n  "name": "x",\n  "db": {"port": 5000, "hosts": ["a", "b"]}\n}\n') == {
        "name": "x",
        "db": {"port": 5000, "hosts": ["a", "b"]},
    }


def test_parse_block_scalars():
    yaml_text = """
    literal: |
      line one
      line two
    literal_strip: |-
      line one
      line two
    literal_keep: |+
      kept

    folded: >-
      part one
      part two

      second paragraph
    folded_more_indented: >
      normal
        indented
      normal again
    indentation_indicator: |2
       leading space
    """
    result = parse_yaml_str(yaml_text)
    assert result["literal"] == "line one\nline two\n"
    assert result["literal_strip"] == "line one\nline two"
    assert result["literal_keep"] == "kept\n\n"
    assert result["folded"] == "part one part two\nsecond paragraph"
    assert result["folded_more_indented"] == "normal\n  indented\nnormal again\n"
    assert result["indentation_indicator"] == " leading space\n"


def test_parse_multiline_scalars():
    yaml_text = """
    plain: this is a long
      plain scalar

      with a paragraph
    double: "first
      second \\
      third"
    single: 'one
      two'
    """
    assert parse_yaml_str(yaml_text) == {
        "plain": "this is a long plain scalar\nwith a paragraph",
        "double": "first second third",
        "single": "one two",
    }


def test_anchors_aliases_and_merge_keys():
    yaml_text = """
    defaults: &defaults
      host: localhost
      port: 5432
    extra: &extra {timeout: 5}
    dev:
      <<: *defaults
      port: 5433
    test:
      <<: [*extra, *defaults]
      name: test
    port: &port 8080
    other_port: *port
    """
    result = parse_yaml_str(yaml_text)
    assert result["dev"] == {"host": "localhost", "port": 5433}
    assert result["test"] == {"timeout": 5, "host": "localhost", "port": 5432, "name": "test"}
    assert result["other_port"] == 8080


def test_explicit_tags():
    yaml_text = """
    as_str: !!str 123
    as_int: !!int "42"
    as_float: !!float 1
    as_bool: !!bool "yes"
    as_null: !!null ""
    as_binary: !!binary aGVsbG8=
    as_set: !!set {a, b}
    as_omap: !!omap [x: 1, y: 2]
    """
    assert parse_yaml_str(yaml_text) == {
        "as_str": "123",
        "as_int": 42,
        "as_float": 1.0,
        "as_bool": True,
        "as_null": None,
        "as_binary": b"hello",
        "as_set": {"a", "b"},
        "as_omap": [("x", 1), ("y", 2)],
    }


def test_escape_sequences():
    assert load('a: "\\x41\\u00e9\\U0001F600\\e\\a\\N\\_\\L\\P\\/\\ "') == {
        "a": "A\u00e9\U0001f600\x1b\x07\x85\xa0\u2028\u2029/ "
    }


def test_bom_and_windows_line_endings():
    assert parse_yaml_str("\ufeffname: x\r\nport: 1\r\n") == {"name": "x", "port": 1}


def test_parser_error_contains_file_name_and_position(tmp_path):
    config_path = tmp_path / "broken.yaml"
    config_path.write_text("a: 1\nb: c: d\n")
    with open(config_path) as file, pytest.raises(ParserError, match=r'broken\.yaml", line 2, column 5'):
        YamlFileParser().parse(file)


@pytest.mark.parametrize(
    "invalid_yaml",
    [
        'key: "unterminated',
        "key: 'unterminated",
        "a: 1\n\tb: 2",
        "a: 1\n  b: 2",
        "invalid_line_without_colon\nkey: value",
        "list: [1, 2",
        "- item1\n- item2",
        "a: b: c",
        "a: - b",
        "a: 1\n---\nb: 2",
        'a: "\\xZZ"',
        'a: "\\q"',
        'a: "\\UFFFFFFFF"',
        "a: *undefined",
        "a: &x 1\nb: &x 2",
        "a: !custom x",
        "a: !!int abc",
        "[1, 2]: x",
        "a: @x",
        "a: |0\n  x",
        "plain scalar document",
    ],
)
def test_parse_invalid_yaml_raises_parser_error(invalid_yaml: str):
    with pytest.raises(ParserError):
        parse_yaml_str(invalid_yaml)
