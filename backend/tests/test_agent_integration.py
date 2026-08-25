import asyncio
import os

import pytest

from app.agents.tools.base import ToolContext
from app.agents.tools.sql_readonly import SQLReadOnlyTool

pytestmark = [pytest.mark.integration, pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="set RUN_INTEGRATION=1")]


def test_agent_sql_readonly_real_postgres():
    async def execute():
        result = await SQLReadOnlyTool().invoke(ToolContext(None), {"sql": "SELECT extversion FROM pg_extension WHERE extname = 'vector'"})
        assert result.success
        assert result.output["row_count"] == 1
        assert result.output["read_only"] if "read_only" in result.output else True
    asyncio.run(execute(), loop_factory=asyncio.SelectorEventLoop)
