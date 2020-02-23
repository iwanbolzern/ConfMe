import logging

import yaml


def load_yaml(path: str):
    with open(path, 'r') as yml_file:
        try:
            return yaml.safe_load(yml_file)
        except yaml.YAMLError as exc:
            logging.exception(f'Not able to load config yaml from: {path}', exc)