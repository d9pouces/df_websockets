from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.backends.dummy import DummyCache
from django.core.cache.backends.locmem import LocMemCache
from django.core.checks import Error, register

from df_websockets import constants, ws_settings


@register()
def effective_cache_check(app_configs, **kwargs):
    errors = []
    try:
        cache = caches[ws_settings.WEBSOCKET_CACHE_BACKEND]
    except InvalidCacheBackendError:
        errors.append(
            Error(
                f"Invalid cache backend name '{ws_settings.WEBSOCKET_CACHE_BACKEND}'",
                hint="Change the WEBSOCKET_CACHE_BACKEND setting or define this cache backend in the CACHES setting.",
                id="df_websockets.E001",
            )
        )
        cache = None
    if isinstance(cache, DummyCache) or (
        isinstance(cache, LocMemCache)
        and ws_settings.WEBSOCKET_WORKERS != constants.WORKER_THREAD
    ):
        errors.append(
            Error(
                f"Invalid cache backend '{cache.__module__}.{cache.__class__.__name__}'",
                hint=f"Update CACHES['{ws_settings.WEBSOCKET_CACHE_BACKEND}']"
                f" or define a new cache backend in the CACHES setting and update"
                f" the WEBSOCKET_CACHE_BACKEND setting.",
                obj=cache,
                id="df_websockets.E002",
            )
        )

    return errors
