# import os
# from dataclasses import dataclass
# from typing import Tuple, NewType, Sequence, Generic, TypeVar, get_type_hints, Union, List
#
# from yaml_loading import load_yaml
#
#
# class Config:
#     pass
#
#
# class SecretType:
#     __slots__ = ()
#
#     def __new__(cls, *args, **kwds):
#         raise SyntaxError(f'{cls.__name__} is only a marker class and can not be instantiated')
#
#     def __class_getitem__(cls, params):
#         assert len(params) == 2, 'Params must be of length two'
#
#         cls.__key__ = params[0]
#         cls.__value_type__ = params[1]
#
#         return cls
#
#     def __init_subclass__(cls, *args, **kwargs):
#         pass
#
#
# #########################################################################################
#
#
# def configclass(_cls):
#     _cls.__config_class__ = True
#     return dataclass(_cls)
#
#
# @configclass
# class ChildNode(Config):
#     test_tuple: str
#     password: SecretType['orgendwas', str]
#
#
# bla1 = ChildNode
# bla2 = ChildNode
#
#
# @dataclass
# class RootConfig:
#     seed: int
#     childNode: ChildNode
#
#
# config = load_config(RootConfig, path='path_to_config.yaml')
# #########################################################################################
#
# AllScalar = Union[int, float, str]
# can_decode = Union[AllScalar, List[AllScalar]]
#
# type_hints = get_type_hints(RootConfig)
# #config_handler = load_config(RootConfig, path='path_to_config.yaml')
# print(type_hints)
#
# def load_config(config_class, path):
#     pass
#
#
# def _check_union(t, union):
#     return any([union_t == t for union_t in union.__args__])
#
#
# yml_dict = load_yaml('tests/example.yaml')
#
# def _extract_type_dict_information(config_class):
#     types = get_type_hints(config_class)
#     for attr_name, attr_type in types.items():
#         if issubclass(attr_type, Config):
#             types[attr_name] = _extract_type_dict_information(attr_type)
#         elif attr_type == SecretType:
#             pass
#         elif _check_union(attr_type, AllScalar):
#             pass
#         else:
#             raise Exception('Not supported type')
#
#     return types
#
# type_dict = _extract_type_dict_information(RootConfig)
#
#
#
#
# def fill_classes(config_type_root, yaml_head):
#     params = {}
#     for attr_name, attr_type in get_type_hints(config_type_root).items():
#         if issubclass(attr_type, Config):
#             params[attr_name] = fill_classes(attr_type, yaml_head[attr_name])
#         elif attr_type == SecretType:
#             params[attr_name] = attr_type.__value_type__(os.environ[attr_type.__key__])
#         elif _check_union(attr_type, AllScalar):
#             params[attr_name] = attr_type(yaml_head[attr_name])
#
#     return config_type_root(**params)
#
# config = fill_classes(RootConfig, yml_dict)
#
#
# print(config)
#
#
