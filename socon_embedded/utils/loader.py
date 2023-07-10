import copy
import json
import logging
import os

from pathlib import Path
from typing import Union

from yaml import YAMLError, safe_load

from socon_embedded.exceptions import YamlParserError

logger = logging.getLogger(__name__)


def from_json_or_yaml(data, show_content=True):
    """
    Creates a python datastructure from the given data, which can be either
    a JSON or YAML string.
    """
    new_data = None

    try:
        new_data = json.loads(data)
    except json.JSONDecodeError as json_exc:
        try:
            new_data = safe_load(data)
        except YAMLError as yaml_exc:
            raise YamlParserError(
                "We were unable to read either as JSON nor YAML, these are the "
                "errors we got from each:\n"
                f"JSON: {json_exc}\n\n"
                f"YAML: {yaml_exc}\n\n"
                f"Content of the file:\n{new_data}"
                if show_content is True
                else ""
            )

    return new_data


def load_from_file(file: Union[str, os.PathLike], show_content: bool = True):
    """Loads data from a file, which can contain either JSON or YAML."""

    # Transform the file as Path and resolve it. Resolving the file might
    # trigger FileNotFoundError
    file = Path(file).expanduser().resolve(True)

    logger.debug("Loading data from {}".format(file))

    try:
        with open(file, "r") as fp:
            file_data = fp.read()
    except (IOError, OSError) as e:
        raise YamlParserError(
            f"An error occurred while trying to read the file: {file}"
        ) from e

    parsed_data = from_json_or_yaml(data=file_data, show_content=show_content)

    return copy.deepcopy(parsed_data)
