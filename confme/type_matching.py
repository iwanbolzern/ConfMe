from typing import get_type_hints

from config import Config





def match( config_class, yaml_head):
    types = get_type_hints(config_class)