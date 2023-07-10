from socon.core.manager import Hook
from pydantic import BaseModel


class ActionShema(BaseModel):
    pass


class ActionBase(Hook):
    pass
