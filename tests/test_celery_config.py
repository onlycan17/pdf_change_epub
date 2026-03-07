import importlib


def test_celery_task_limits_are_unset(monkeypatch):
    monkeypatch.delenv("APP_CELERY_TASK_TIME_LIMIT_SECONDS", raising=False)
    monkeypatch.delenv("APP_CELERY_TASK_SOFT_TIME_LIMIT_SECONDS", raising=False)
    monkeypatch.delenv("APP_CELERY_VISIBILITY_TIMEOUT_SECONDS", raising=False)

    module = importlib.import_module("app.celery_config")
    module = importlib.reload(module)

    assert module.celery_app.conf.task_time_limit is None
    assert module.celery_app.conf.task_soft_time_limit is None
    assert module.celery_app.conf.broker_transport_options == {
        "visibility_timeout": 604800
    }
    assert module.celery_app.conf.result_backend_transport_options == {
        "visibility_timeout": 604800
    }


def test_celery_visibility_timeout_can_be_overridden(monkeypatch):
    monkeypatch.setenv("APP_CELERY_VISIBILITY_TIMEOUT_SECONDS", "864000")

    module = importlib.import_module("app.celery_config")
    module = importlib.reload(module)

    assert module.celery_app.conf.broker_transport_options == {
        "visibility_timeout": 864000
    }
    assert module.celery_app.conf.result_backend_transport_options == {
        "visibility_timeout": 864000
    }
