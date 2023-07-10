import os

from pathlib import Path
from typing import Any, Dict, Union

from jinja2 import Environment, FileSystemLoader


def jinja_resolve(file: Union[str, os.PathLike], context: Dict[str, Any]) -> str:
    """Resolve a file with the given context"""
    file = Path(file).expanduser().resolve()
    template_loader = FileSystemLoader(file.parent)
    env = Environment(loader=template_loader)
    template = env.get_template(file.name)
    return template.render(**context)
