# ConfMe: Configuration Made Easy 💖

[![image](https://img.shields.io/pypi/v/confme?color=blue)](https://pypi.org/project/confme/) [![image](https://img.shields.io/pypi/l/confme)](https://pypi.org/project/confme/) [![image](https://github.com/iwanbolzern/ConfMe/workflows/Test/badge.svg?branch=master)](https://pypi.org/project/confme/)
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
    name: str
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
- [Enum](#enum)

### Secret
With the Secret annotation you can inject secrets from environment variables directly into your configuration structure. This is especially handy when you're deploying applications by using docker. Therefore, let's extend the previous example with a Secret annotation:

```python
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
* ```ClosedRange(2, 3)``` will include 2 and 3
* ```OpenRange(2, 3)``` will not include 2 and 3

If you want to have a mixture of both, e.g. include 2 but exclude 3 use MixedRange:
* ```MixedRange(ge=2, lt=3)``` will include 2 but exclude 3

```python
from confme import BaseConfig
from confme.annotation import ClosedRange

class DatabaseConfig(BaseConfig):
    ...
    password: int = ClosedRange(2, 3)
```

### Enum

If a Python Enum is set as type annotation, ConfMe expect to find the enum value in the configuration file.

```python
from confme import BaseConfig
from enum import Enum

class DatabaseConnection(Enum):
    TCP = 'tcp'
    UDP = 'udp'

class DatabaseConfig(BaseConfig):
    ...
    connection_type: DatabaseConnection
```

## Switching configuration based on Environment
A very common situation is that configurations must be changed based on the execution environment (dev, test, prod). This can be accomplished 
by registering a folder with one .yaml file per environment and seting the `ENV` environment variable to the value you need. An example could look 
like this:  

Let's assume we have three environments (dev, test, prod) and one configuration file per environment in the following folder structure:
```
project
│
└───config
│   │   my_prod_config.yaml
│   │   my_test_config.yaml
│   │   my_dev_config.yaml
│   
└───src
│   │   app.py
│   │   my_config.py
```
The definition of `my_config.py` is equivalent to the one used in the basic introduction section and `app.py` uses our configuration the 
following way:
```python
# we register the folder where ConfME can find the configuration files
MyConfig.register_folder(Path(__file__).parent / '../config')
...

# we access the instance of the corresponding configuration file anywhere in our project. 
my_config = MyConfig.get()
print(f'Using database connection {my_config.database.host} '
      f'on port {my_config.database.port}')
```
If now one of the following environment variables (precedence in descending order): `['env', 'environment', 'environ', 'stage']` is 
set e.g. `export ENV=prod` it will load the configuration file with `prod` in its name.

## Parameter overwrite
In addition to loading configuration parameters from the configuration file, they can be passed/overwritten from the command line or environment variables. Thereby, the following precedences apply (lower number means higher precedence):
1. **Command Line Arguments**: Check if parameter is set as command line argument. If not go one line done...
2. **Environment Variables**: Check if parameter is set as environment variable. If not go one line done...
3. **Configuration File**: If value was not found in one of the previous sources, it will check in the configuration file.

### Overwrite Parameters from Command Line
Especially in the Data Science and Machine Learning area it is useful to pass certain parameters for experimental purposes as command line arguments. Therefore, all properties defined in the configuration classes are automatically offered as command line arguments in the following format:

**my_program.py:**

```python
from confme import BaseConfig

class DatabaseConfig(BaseConfig):
    host: str
    port: int
    user: str

class MyConfig(BaseConfig):
    name: int
    database: DatabaseConfig

config = MyConfig.load('test.yaml')
```

When you now start your program from the command line with the ```++help``` argument, you get the full list of all configuration options. **CAVEAT!** In order to not interfere with other cli tools, the prefix - was changed to +:
```shell
$ python my_program.py --help
usage: my_program.py [+h] [++name NAME] [++database.host DATABASE.HOST] [++database.port DATABASE.PORT] [++database.user DATABASE.USER]

optional arguments:
  +h, ++help            show this help message and exit

Configuration Parameters:
  With the parameters specified bellow, the configuration values from the config file can be overwritten.

  ++name NAME
  ++database.host DATABASE.HOST
  ++database.port DATABASE.PORT
  ++database.user DATABASE.USER
```

### Overwrite Parameters with Environment Variables
Likewise to overwriting parameters from the commandline you can also overwrite by passing environment variables. Therefore, simply set the environment variable in the same format as it would be passed as command line arguments and run your application:
```shell
$ export database.host=localhost
$ python my_programm.py
```

## LICENSE

ConfMe is released under the [MIT](LICENSE) license.

