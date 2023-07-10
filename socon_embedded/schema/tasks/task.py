from __future__ import annotations

from typing import List, Literal, Type
from socon_embedded.exceptions import ParserError

from socon_embedded.schema.base import Base, Nameable, get_field_names

from pydantic import BaseModel, Field, model_validator


class Task(Base, Nameable):
    """Call a module (action) with specific arguments and other parameters"""
    action: str
    args: dict = {}

    @model_validator(mode="before")
    def preprocess_action(cls, values):
        action = None
        args = {}

        if 'action' in values:
            action = values['action']
        if 'args' in values:
            args = values['args']

        # filter out task attributes so we're only querying unrecognized keys as actions/modules
        non_task_values = dict(
            (k, v) for k, v in values.items()
            if (k not in get_field_names(Task))
        )

        # walk the filtered input dictionary to see if we recognize a module name
        for item, value in non_task_values.items():
            is_action_candidate = False
            if item in ['copy', 'move']:
                is_action_candidate = True

            if is_action_candidate:

                # finding more than one module name is a problem
                if action is not None:
                    raise ParserError(
                        "conflicting action statements: {}, {}".format(
                            action, item
                        )
                    )

                action = item
                args = value

        # if we didn't see any module in the task at all, it's not a task really
        if action is None:
            if non_task_values:  # there was one non-task action, but we couldn't find it
                bad_action = list(non_task_values.keys())[0]
                raise ParserError(
                    "couldn't resolve module/action '{0}'. This often indicates a "
                    "misspelling, missing collection, or "
                    "incorrect module path.".format(bad_action))
            else:
                raise ParserError(
                    "no module/action detected in task."
                )

        # Set the action if no previous error
        values['action'] = action
        values['args'] = args
        return values


class Taskable(BaseModel):
    """
    Make a schema taskable.
    Give the ability to have pre_tasks, post_tasks and tasks
    """

    # Tasks list attribute
    tasks: List[Task] = Field(default_factory=list)
    post_tasks: List[Task] = Field(default_factory=list)

    def merge_tasks(
        self,
        y: Type[Taskable],
        keep: bool,
        tasks_type: Literal["tasks", "post_tasks"]
    ) -> Type[Taskable]:
        """Merge y tasks into x tasks"""
        if keep is False:
            setattr(self, tasks_type, getattr(y, tasks_type))
        else:
            for task in getattr(y, tasks_type):
                if task not in getattr(self, tasks_type):
                    getattr(self, tasks_type).append(task)
        return self
