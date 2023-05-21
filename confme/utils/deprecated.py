import functools
import inspect
import warnings


def log_deprecated(msg: str):
    warnings.simplefilter('always', DeprecationWarning)
    warnings.warn(
        msg,
        category=DeprecationWarning,
        stacklevel=2
    )
    warnings.simplefilter('default', DeprecationWarning)


def deprecated(reason: str = ''):
    def decorator(func):
        if inspect.isclass(func):
            old_init = func.__init__

            @functools.wraps(func.__init__)
            def new_init(*args, **kwargs):
                log_deprecated(f"Call to deprecated class {func.__name__} ({reason}).")
                old_init(*args, **kwargs)
            func.__init__ = new_init
            return func
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                log_deprecated(f"Call to deprecated class {func.__name__} ({reason}).")
                return func(*args, **kwargs)

            return wrapper

    return decorator
