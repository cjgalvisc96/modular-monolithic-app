from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
import pytest_asyncio

from tests.support.containers import build_sqlite_container

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest_asyncio.fixture
async def container(tmp_path) -> AsyncIterator:
    db_file = tmp_path / "test.db"
    c = await build_sqlite_container(str(db_file))
    yield c
    await c.shared.database().dispose()
