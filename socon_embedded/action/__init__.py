from typing import Union

from socon.core.manager import Hook
from pydantic import BaseModel, ConfigDict

from socon_embedded.schema.task import Task


class ActionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActionBase(Hook, abstract=True):

    manager = "ActionManager"
    schema = None

    def __init__(self, task: Task) -> None:
        self._task = task
        self.args = self.schema(**self._task.args)

    def run(self, tasks_vars=None):
        """Run the task"""
        return {"failed": False}

    def cleanup(self, force: bool = False):
        """Method to perform a clean up at the end of an action plugin execution

        Action plugins may override this if they deem necessary
        """
