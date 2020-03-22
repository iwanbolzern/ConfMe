from confme import BaseConfig


class ChildNode(BaseConfig):
    # das ist ein kommentar für den string
    testStr: str  # das ist ein anderer kommentar für den string


class RootConfig(BaseConfig):
    rootValue: int
    childNode: ChildNode


#config = RootConfig.load('tests/test.yaml')


