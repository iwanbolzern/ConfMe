# ConfMe: Configuration Made Easy 💖
[![image](https://img.shields.io/pypi/v/confme?color=blue)](https://pypi.org/project/confme/)
[![image](https://img.shields.io/pypi/l/confme)](https://pypi.org/project/confme/)
[![image](https://github.com/iwanbolzern/ConfMe/workflows/Test/badge.svg?branch=master)](https://pypi.org/project/confme/)
[![image](https://img.shields.io/pypi/pyversions/confme?color=blue)](https://pypi.org/project/confme/)

ConfMe is a simple to use, production ready application configuration management library, which takes into consideration the following three thoughts:
1. Access to configuration values must be safe at runtime. **No ```myconfig['value1']['subvalue']``` anymore!**
2. The configuration must be checked for consistency at startup e.g. type check, range check, ...
3. Secrets shall be injectable from environment variables

ConfMe makes all these features possible with just a few type annotations on plain Python objects.

## Installation
ConfMe can be installed from the official python package repository [pypi](https://pypi.org/project/confme/)
```
pip install confme
```
Or, if you're using pipenv:
```
pipenv install confme
```
Or, if you're using poetry:
```
poetry add confme
```

## Basic Usage of confme
Define your config structure as plain python objects with type annotations:
```python
from confme import BaseConfig

class DatabaseConfig(BaseConfig):
    host: str
    port: int
    user: str

class MyConfig(BaseConfig):
    name: int
    database: DatabaseConfig
```
Create a configuration yaml file with the same structure as your configuration classes have:
```yaml
name: "Database Application"
database:
    host: "localhost"
    port: 5000
    user: "any-db-user"
```
Load the yaml file into your Python object structure and access it in a secure manner:
```python
my_config = MyConfig.load('config.yaml')

print(f'Using database connection {my_config.database.host} '
      f'on port {my_config.database.port}')
```
In the background the yaml file is parsed and mapped to the defined object structure. While mapping the values to object properties, type checks are performed. If a value is not available or is not of the correct type, an error is generated already when the configuration is loaded.

## Supported Annotations
ConfMe is based on pydantic and supports all annotations provided by pydantic. The most important annotations are listed and explain bellow. For the whole list, please checkout [Field Types](https://pydantic-docs.helpmanual.io/usage/types/):
- str
- int
- float
- bool
- typing.List[x]
- typing.Optional[x]
- [Secret](#secret)
- [Range](#range)
- [enum.Enum]()
- [enum.IntEnum]()

### Secret
With the Secret annotation you can inject secrets from environment variables directly into your configuration structure. This is especially handy when you're deploying applications by using docker. Therefore, let's extend the previous example with a Secret annotation:
```python
...
from confme import BaseConfig
from confme.annotation import Secret

class DatabaseConfig(BaseConfig):
    ...
    password: str = Secret('highSecurePassword')
```
Now set the password to the defined environment variable:
```bash
export highSecurePassword="This is my password"
```
Load your config and check for the injected password.
```
my_config = MyConfig.load('config.yaml')
print(f'My password is: {my_config.database.password}')
```

### Range
ConfME supports OpenRange, ClosedRange and MixedRange values. The terms open and close are similar to open and closed intervals in mathematics. This means, if you want to include the lower and upper range use ClosedRange otherwise OpenRange:  
ClosedRange(2, 3) will include 2 and 3  
OpenRange(2, 3) will not include 2 and 3

If you want to have a mixture of both, e.g. include 2 but exclude 3 use MixedRange:  
MixedRange(ge=2, lt=3) will include 2 but exclude 3

```python
...
from confme import BaseConfig
from confme.annotation import ClosedRange

class DatabaseConfig(BaseConfig):
    ...
    password:int = ClosedRange(2, 3)
```

### SELECTION[args...]



## LICENSE
ConfMe is released under the [MIT](LICENSE) license.