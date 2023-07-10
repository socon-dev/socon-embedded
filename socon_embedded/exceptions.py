"""socon-embedded exceptions"""


class YamlParserError(Exception):
    """something was detected early that is wrong about app config gile"""


class YamlFormatError(Exception):
    """Raised when the application registry yaml format is wrong"""


class ApplicationRegistryNotReady(Exception):
    """Raised when the application registry is not ready"""


class ParserError(Exception):
    """Raised when we cannot passe or load a YAML/Json file"""


class TaskExecutionError(Exception):
    """Raised when a task failed for any exception"""
