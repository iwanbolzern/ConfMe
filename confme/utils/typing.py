from typing import Dict

from pydantic.main import ModelMetaclass
from pydantic.schema import model_schema


def _create_dict(schema_head: Dict, definitions: Dict):
    schema_dict = {}
    if 'type' in schema_head and schema_head['type'] == 'object':
        for key, value in schema_head['properties'].items():
            if 'allOf' in value:
                sub_schema = value['allOf'][0]['$ref'].replace('#/definitions/', '')
                schema_dict[key] = _create_dict(definitions[sub_schema], definitions)
            else:
                schema_dict[key] = None
    else:
        return None
    return schema_dict


def get_schema(config_cls: ModelMetaclass):
    schema = model_schema(config_cls)
    definitions = schema['definitions'] if 'definitions' in schema else {}
    return _create_dict(schema, definitions)
