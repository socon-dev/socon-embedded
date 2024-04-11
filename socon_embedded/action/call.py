from typing import Optional

from socon.core.management import call_command
from socon.core.management.base import CommandError
from socon_embedded.action import ActionBase, ActionSchema


class Schema(ActionSchema):
    cmd: str
    argv: Optional[list[str]] = []


class CallCommandAction(ActionBase):
    name = "call_command"
    schema = Schema

    def run(self, tasks_vars=None):
        result = super().run(tasks_vars)
        try:
            call_command(self.args.cmd, *self.args.argv)
        except CommandError as e:
            result["failed"] = True
            result["msg"] = f"Command error: {e}"
        return result
