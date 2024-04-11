from socon_embedded.action import ActionBase, ActionSchema


class MoveActionShema(ActionSchema):
    pass


class MoveAction(ActionBase):
    name = "move"
    action_schema = MoveActionShema

    def run(self, tasks_vars=None):
        pass
