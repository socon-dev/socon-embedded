import os
import tempfile
import json
import shutil

from pathlib import Path
from typing import Optional

from socon_embedded.action import ActionBase, ActionSchema

from pydantic import model_validator

from socon_embedded.utils.converter import to_bytes


class CopySchema(ActionSchema):
    dest: str
    src: Optional[str] = None
    content: Optional[str] = None

    @model_validator(mode="after")
    def basic_validation(self):
        """If src is a directory, dest must be a directory too."""
        if self.src is None and self.content is None:
            raise ValueError("'src' or 'content' field must be supply")
        if self.src is not None and self.content is not None:
            raise ValueError("Only 'src' or 'content' must be supply at the same time")
        if self.content is not None and Path(self.dest).is_dir():
            raise ValueError("Can not use 'content' with a dir as 'dest'")
        return self


class CopyAction(ActionBase):
    name = "copy"
    schema = CopySchema

    def run(self, tasks_vars=None):
        if tasks_vars is None:
            tasks_vars = dict()

        # Result of the task stored in a dictionary
        result = super().run(tasks_vars)

        source = self.args.src
        content = self.args.content

        # Define content_tempfile in case we set it after finding content populated.
        content_tempfile = None

        if content is not None:
            try:
                # If content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string to write it out.
                if isinstance(content, dict) or isinstance(content, list):
                    content_tempfile = self._create_content_tempfile(
                        json.dumps(content)
                    )
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception as err:
                result["failed"] = True
                result["msg"] = f"could not write content temp file: {err}"
                return result

        source = Path(source).expanduser().absolute()
        if source.is_dir():
            shutil.copytree(source, self.args.dest, dirs_exist_ok=True)
        else:
            shutil.copy2(source, self.args.dest)

        return result

    def _create_content_tempfile(self, content):
        """Create a tempfile containing defined content"""
        fd, content_tempfile = tempfile.mkstemp(prefix=".")
        f = os.fdopen(fd, "wb")
        content = to_bytes(content)
        try:
            f.write(content)
        except Exception as err:
            os.remove(content_tempfile)
            raise Exception(err)
        finally:
            f.close()
        return content_tempfile
