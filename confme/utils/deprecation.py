import functools
import warnings


def deprecated(comment: str = ''):
    return functools.partial(_deprecated_func, comment=comment)


def deprecated_cls(comment: str = ''):
    return functools.partial(_deprecated_cls, comment=comment)


def _deprecated_func(func, comment: str):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn(f'Call to deprecated function {func.__name__}.\n'
                      f'Comment: {comment}',
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func


def _deprecated_cls(cls, comment: str):
    warnings.simplefilter('always', DeprecationWarning)  # turn off filter
    warnings.warn(f'Call to deprecated class {cls.__name__}.\n'
                  f'Comment: {comment}',
                  category=DeprecationWarning,
                  stacklevel=2)
    warnings.simplefilter('default', DeprecationWarning)  # reset filter
    return cls
