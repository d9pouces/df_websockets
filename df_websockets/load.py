from df_websockets import constants, ws_settings


def load_celery():
    if ws_settings.WEBSOCKET_WORKERS == constants.WORKER_CELERY:
        # noinspection PyUnresolvedReferences
        import df_websockets.celery
