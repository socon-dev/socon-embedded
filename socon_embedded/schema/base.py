import os
from typing import Type, Union
from pydantic import BaseModel

from socon_embedded.utils.jinja import jinja_resolve
from socon_embedded.utils.loader import from_json_or_yaml, load_from_file


def get_field_names(model: Type[BaseModel]) -> list[str]:
    return list(model.model_fields.keys())


class Base(BaseModel):

    @classmethod
    def load(cls, file: Union[str, os.PathLike], context: dict = {}):
        """Create a schema from a yaml/json file"""
        if context:
            content = jinja_resolve(file, context)
            data = from_json_or_yaml(content)
        else:
            data = load_from_file(file)
        return cls(**data)


class Nameable(BaseModel):
    name: str
