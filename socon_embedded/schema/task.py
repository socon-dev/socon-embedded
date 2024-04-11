from __future__ import annotations

from typing import List, Literal, Optional, Type

from socon.core.registry import projects

from socon_embedded.exceptions import ParserError
from socon_embedded.managers import get_action_manager
from socon_embedded.schema.base import Base, Nameable, get_field_names

from pydantic import BaseModel, Field, model_validator


class Task(Base, Nameable):
    """Call a module (action) with specific arguments and other parameters"""

    action: Type
    args: dict = {}

    retries: Optional[int] = 0
    timeout: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def preprocess_action(cls, values):
        action = None
        args = {}

        if "action" in values:
            action = values["action"]
        if "args" in values:
            args = values["args"]

        # filter out task attributes so we're only querying unrecognized keys as actions/modules
        non_task_values = dict(
            (k, v) for k, v in values.items() if (k not in get_field_names(Task))
        )

        # walk the filtered input dictionary to see if we recognize a module name
        action_manager = get_action_manager()
        for item, value in non_task_values.items():
            is_action_candidate = False
            if item in action_manager.get_hooks_name():
                is_action_candidate = True

            if is_action_candidate:

                # finding more than one module name is a problem
                if action is not None:
                    raise ParserError(
                        "conflicting action statements: {}, {}".format(action, item)
                    )

                action = item
                args = value

        # if we didn't see any module in the task at all, it's not a task really
        if action is None:
            if (
                non_task_values
            ):  # there was one non-task action, but we couldn't find it
                bad_action = list(non_task_values.keys())[0]
                raise ParserError(
                    "couldn't resolve module/action '{0}'. This often indicates a "
                    "misspelling, missing collection, or "
                    "incorrect module path.".format(bad_action)
                )
            else:
                raise ParserError("no module/action detected in task.")

        try:
            project_config = projects.get_project_config_by_env()
        except LookupError:
            project_config = None
        action = action_manager.search_hook_impl(action, project_config)

        # Set the action if no previous error
        values["action"] = action
        values["args"] = args
        return values

    @model_validator(mode="after")
    def post_process_action(self):
        """Validate the action schema"""
        self.action = self.action(self)
        return self


class Taskable(BaseModel):
    """
    Make a schema taskable.
    Give the ability to have pre_tasks, post_tasks and tasks
    """

    # Tasks list attribute
    tasks: List[Task] = Field(default_factory=list)
    post_tasks: List[Task] = Field(default_factory=list)

    def merge_tasks(
        self, y: Type[Taskable], keep: bool, tasks_type: Literal["tasks", "post_tasks"]
    ) -> Type[Taskable]:
        """Merge y tasks into x tasks"""
        if keep is False:
            setattr(self, tasks_type, getattr(y, tasks_type))
        else:
            for task in getattr(y, tasks_type):
                if task not in getattr(self, tasks_type):
                    getattr(self, tasks_type).append(task)
        return self
