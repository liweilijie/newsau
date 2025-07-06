import redis

from importlib import import_module
from typing import Any
from collections.abc import Callable


REDIS_CLS = redis.StrictRedis
REDIS_ENCODING = "utf-8"
# Sane connection defaults.
REDIS_PARAMS = {
    "socket_timeout": 30,
    "socket_connect_timeout": 30,
    "retry_on_timeout": True,
    "encoding": REDIS_ENCODING,
}
REDIS_CONCURRENT_REQUESTS = 16

SCHEDULER_QUEUE_KEY = "%(spider)s:requests"
SCHEDULER_PERSIST = False
START_URLS_KEY = "%(name)spider:start_urls"
MAX_IDLE_TIME = 0

# Shortcut maps 'setting name' -> 'parmater name'.
SETTINGS_PARAMS_MAP = {
    "REDIS_URL": "url",
    "REDIS_HOST": "host",
    "REDIS_PORT": "port",
    "REDIS_DB": "db",
    "REDIS_ENCODING": "encoding",
}

SETTINGS_PARAMS_MAP["REDIS_DECODE_RESPONSES"] = "decode_responses"


def get_redis_from_settings(settings):
    """Returns a redis client instance from given Scrapy settings object.

    This function uses ``get_client`` to instantiate the client and uses
    ``defaults.REDIS_PARAMS`` global as defaults values for the parameters. You
    can override them using the ``REDIS_PARAMS`` setting.

    Parameters
    ----------
    settings : Settings
        A scrapy settings object. See the supported settings below.

    Returns
    -------
    server
        Redis client instance.

    Other Parameters
    ----------------
    REDIS_URL : str, optional
        Server connection URL.
    REDIS_HOST : str, optional
        Server host.
    REDIS_PORT : str, optional
        Server port.
    REDIS_DB : int, optional
        Server database
    REDIS_ENCODING : str, optional
        Data encoding.
    REDIS_PARAMS : dict, optional
        Additional client parameters.

    Python 3 Only
    ----------------
    REDIS_DECODE_RESPONSES : bool, optional
        Sets the `decode_responses` kwarg in Redis cls ctor

    """
    params = REDIS_PARAMS.copy()
    params.update(settings.getdict("REDIS_PARAMS"))
    # XXX: Deprecate REDIS_* settings.
    for source, dest in SETTINGS_PARAMS_MAP.items():
        val = settings.get(source)
        if val:
            params[dest] = val

    # Allow ``redis_cls`` to be a path to a class.
    if isinstance(params.get("redis_cls"), str):
        params["redis_cls"] = load_object(params["redis_cls"])

    return get_redis(**params)

# Backwards compatible alias.
from_settings = get_redis_from_settings

def get_redis(**kwargs):
    """Returns a redis client instance.

    Parameters
    ----------
    redis_cls : class, optional
        Defaults to ``redis.StrictRedis``.
    url : str, optional
        If given, ``redis_cls.from_url`` is used to instantiate the class.
    **kwargs
        Extra parameters to be passed to the ``redis_cls`` class.

    Returns
    -------
    server
        Redis client instance.

    """
    redis_cls = kwargs.pop("redis_cls", REDIS_CLS)
    url = kwargs.pop("url", None)
    print(f'get_redis {url}, kwargs {kwargs}')
    if url:
        return redis_cls.from_url(url, **kwargs)
    else:
        return redis_cls(**kwargs)


def load_object(path: str | Callable[..., Any]) -> Any:
    """Load an object given its absolute object path, and return it.

    The object can be the import path of a class, function, variable or an
    instance, e.g. 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware'.

    If ``path`` is not a string, but is a callable object, such as a class or
    a function, then return it as is.
    """

    if not isinstance(path, str):
        if callable(path):
            return path
        raise TypeError(
            f"Unexpected argument type, expected string or object, got: {type(path)}"
        )

    try:
        dot = path.rindex(".")
    except ValueError:
        raise ValueError(f"Error loading object '{path}': not a full path")

    module, name = path[:dot], path[dot + 1 :]
    mod = import_module(module)

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError(f"Module '{module}' doesn't define any object named '{name}'")

    return obj

