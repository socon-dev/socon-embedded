from socon_embedded.action import ActionBase
from pydantic import BaseModel


class CustomSchema(BaseModel):
    test: str


class CustomAction(ActionBase):
    name = "custom_action"
    schema = CustomSchema

    def run(self, tasks_vars=None):
        result = super().run(tasks_vars)
        result["discoverd"] = True
        return result
