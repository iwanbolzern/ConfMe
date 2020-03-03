# ConfMe: Configuration Made Easy 💖
![Python package](https://github.com/iwanbolzern/confme/workflows/Python%20package/badge.svg)

ConfMe is a simple to use, production ready application configuration management library, which takes into consideration the following three thoughts:
1. Access to configuration values must be safe at runtime. **No ```myconfig['value1']['subvalue']``` anymore!**
2. The configuration must be checked for consistency at startup e.g. type check, range check, ...
3. Secrets shall be injectable from environment variables

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
from confme import configclass, load_config

@configclass
class DatabaseConfig:
    host: str
    port: int
    user: str

@configclass
class MyConfig:
    name: int
    database: DatabaseConfig
```
Create a configuration yaml file with the same structure as your classes have:
```yaml
name: "Database Application"
database:
    host: "localhost"
    port: 5000
    user: "any-db-user"
```
Load the yaml file into your Python object structure and access it in a secure manner:
```python
my_config = load_config(MyConfig, 'config.yaml')

print(f'Using database connection {my_config.database.host} '
      f'on port {my_config.database.port}')
```
In the background the yaml file is parsed and mapped to the defined object structure. While mapping the values to object properties, type checks are performed. If a value is not available or is not of the correct type, an error is generated already when the configuration is loaded.

## Supported Annotations
At the moment the following type annotations are supported:
- str
- int
- float
- [Secret](#Secret)
- Range

### Secret['ENV_NAME', TYPE]
To inject secrets from environment variables into the configuration structure the Secret annotation should be used. This is especially handy when you're deploying applications by using docker. Therefore, let's extend the previous example with a Secret annotation:
```python
...
from confme import configclass, load_config
from confme.annotation import Secret

@configclass
class DatabaseConfig:
    ...
    password: Secret['highSecurePassword', str]
```
Now set the password to the defined environment variable:
```bash
export highSecurePassword="This is my password"
```
Load your config and check for the injected password.
```
my_config = load_config(MyConfig, 'config.yaml')
print(f'My password is: {my_config.database.password}')
```

### Range[NUMBER_TYPE, FROM, TO]
```python
...
from confme import configclass, load_config
from confme.annotation import Secret

@configclass
class DatabaseConfig:
    ...
    password: Range[int, 2, 3]
```

### SELECTION[args...]



## LICENSE
ConfMe is released under the [MIT](LICENSE) license.