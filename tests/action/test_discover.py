import os
import pytest

from unittest import mock

from socon.core.exceptions import HookNotFound

from socon_embedded.exceptions import ParserError
from socon_embedded.schema.task import Task


class TestDiscoverAction:

    def test_discover_custom_action_not_found(self):
        with pytest.raises(HookNotFound):
            Task(**{"name": "Test discover", "custom_action": {"test": "test"}})

    @mock.patch.dict(os.environ, {"SOCON_ACTIVE_PROJECT": "test_project"})
    def test_discover_custom_action_in_project(self):
        Task(**{"name": "Test discover", "custom_action": {"test": "test"}})
