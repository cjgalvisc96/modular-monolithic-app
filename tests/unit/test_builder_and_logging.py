import logging

from todo_app.core.logging import configure_logging
from todo_app.presentation.api.app import ApiBuilder


def test_configure_logging_sets_level():
    configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
    configure_logging("not-a-level")  # falls back to INFO


def test_mount_di_container_returns_builder():
    builder = ApiBuilder()
    same = builder.mount_di_container()
    assert same is builder
    new_container = builder._container
    assert builder.mount_di_container(new_container) is builder
