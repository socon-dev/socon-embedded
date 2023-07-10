import codecs
import re

from ast import literal_eval

from socon_embedded.utils.converter import to_text

# Decode escapes adapted from rspeer's answer here:
# http://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python
_HEXCHAR = "[a-fA-F0-9]"
_ESCAPE_SEQUENCE_RE = re.compile(
    r"""
    ( \\U{0}           # 8-digit hex escapes
    | \\u{1}           # 4-digit hex escapes
    | \\x{2}           # 2-digit hex escapes
    | \\N\{{[^}}]+\}}  # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )""".format(
        _HEXCHAR * 8, _HEXCHAR * 4, _HEXCHAR * 2
    ),
    re.UNICODE | re.VERBOSE,
)


def _decode_escapes(s: str) -> str:
    def decode_match(match):
        return codecs.decode(match.group(0), "unicode-escape")

    return _ESCAPE_SEQUENCE_RE.sub(decode_match, s)


def parse_key_value(args: str) -> dict:
    """Convert a string of key/value items to a dict"""
    args = to_text(args, nonstring="passthru")
    kwargs = {}

    if args is not None:
        splitted_args = split_args(args)
        for arg in splitted_args:
            arg = _decode_escapes(arg).split("=")
            key, value = arg[0], arg[1]

            # unquote the value if necessary
            if (
                len(value) > 1
                and value[0] == value[-1]
                and value[0] in ('"', "'")
                and value[-2] != "\\"
            ):
                value = value[1:-1]

            if value.startswith(("[", "{")):
                try:
                    evald = literal_eval(value)
                except (ValueError, SyntaxError):
                    continue
                if isinstance(evald, (dict, list)):
                    value = evald

            kwargs[key] = value

    return kwargs


def split_args(args: str) -> list:
    """Split args on whitespace and other elements"""
    if not args:
        return []

    # the list of params parsed out of the arg string
    # this is going to be the result value when we are done
    return [p for p in re.findall(r"(?:[^\s]+=.+?(?=\s+\w+=|$))", args, re.DOTALL)]
