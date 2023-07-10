from typing import Dict, Type

from pydantic import BaseModel


def _create_dict(schema_head: Dict, definitions: Dict):
    schema_dict = {}
    if 'type' in schema_head and schema_head['type'] == 'object':
        for key, value in schema_head['properties'].items():
            if '$ref' in value:
                sub_schema = value['$ref'].replace('#/$defs/', '')
                schema_dict[key] = _create_dict(definitions[sub_schema], definitions)
            else:
                schema_dict[key] = None
    else:
        return None
    return schema_dict


def get_schema(config_cls: Type[BaseModel]):
    schema = config_cls.model_json_schema()
    definitions = schema['$defs'] if '$defs' in schema else {}
    return _create_dict(schema, definitions)
