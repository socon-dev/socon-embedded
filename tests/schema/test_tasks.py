from _pytest.tmpdir import tmp_path_factory
from pydantic import ValidationError
import yaml

from pathlib import Path
from socon_embedded.exceptions import ParserError
from socon_embedded.schema.task import Task

import pytest


class TestTaskSchema:

    def _load_task(self, file: Path) -> Task:
        with open(file, "r") as fp:
            data = yaml.safe_load(fp)
        return Task(**data)

    def test_bad_action_module(self, datafix_dir):
        msg = "couldn't resolve module/action 'not_exist'"
        with pytest.raises(ParserError, match=msg):
            self._load_task(datafix_dir / "bad_action.yml")

    def test_no_action_module(self, datafix_dir):
        msg = "no module/action detected in task"
        with pytest.raises(ParserError, match=msg):
            self._load_task(datafix_dir / "no_action.yml")

    def test_with_action_module_set(self, datafix_dir):
        task = self._load_task(datafix_dir / "set_action.yml")
        assert task.action.name == "copy"

    def test_autodetect_action_with_args(self, datafix_dir):
        task = self._load_task(datafix_dir / "copy_schema.yml")
        assert task.action.name == "copy"
        assert task.args == {"src": "a", "dest": "b"}

    def test_mulitple_valid_action(self, datafix_dir):
        msg = "conflicting action statements"
        with pytest.raises(ParserError, match=msg):
            self._load_task(datafix_dir / "multiple_valid_action.yml")

    def test_check_action_schema_validation(self, datafix_dir):
        msg = "extra_forbidden"
        with pytest.raises(ValidationError, match=msg):
            self._load_task(datafix_dir / "action_extra_args.yml")


class TestCopyActionTask:

    def test_content_with_dest_as_dir(self, tmp_path):
        d = tmp_path / "sub"
        d.mkdir()
        msg = "Can not use 'content' with a dir as 'dest'"
        with pytest.raises(ValidationError, match=msg):
            Task(
                **{
                    "name": "test",
                    "copy": {"content": "File content", "dest": d.as_posix()},
                }
            )

    def test_mutual_exclusive_src_content(self):
        msg = "Only 'src' or 'content' must be supply at the same time"
        with pytest.raises(ValidationError, match=msg):
            Task(**{"name": "test", "copy": {"src": "", "content": "", "dest": ""}})

    def test_src_or_content_must_be_supply(self):
        msg = "'src' or 'content' field must be supply"
        with pytest.raises(ValidationError, match=msg):
            Task(**{"name": "test", "copy": {"dest": ""}})
