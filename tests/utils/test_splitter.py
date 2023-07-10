import pytest

from socon_embedded.utils.parser import parse_key_value, split_args


# A list of arguments that can be passed as a command line arguments
SPLIT_DATA = (
    (None, [], {}),
    ("", [], {}),
    ("a=b", ["a=b"], {"a": "b"}),
    ("a=['a', 'b']", ["a=['a', 'b']"], {"a": ["a", "b"]}),
    ("a=\"['a', 'b']\"", ["a=\"['a', 'b']\""], {"a": ["a", "b"]}),
    ('a="foo bar"', ['a="foo bar"'], {"a": "foo bar"}),
    ('a=b c="foo bar"', ["a=b", 'c="foo bar"'], {"a": "b", "c": "foo bar"}),
    (
        'a="echo \\"hello world\\"" b=bar',
        ['a="echo \\"hello world\\""', "b=bar"],
        {"a": 'echo "hello world"', "b": "bar"},
    ),
    ('a="nest\'ed"', ['a="nest\'ed"'], {"a": "nest'ed"}),
    ('a="multi\nline"', ['a="multi\nline"'], {"a": "multi\nline"}),
    ('a="blank\n\nline"', ['a="blank\n\nline"'], {"a": "blank\n\nline"}),
    ('a="blank\n\n\nlines"', ['a="blank\n\n\nlines"'], {"a": "blank\n\n\nlines"}),
    (
        'a="a long\nmessage\\\nabout a thing\n"',
        ['a="a long\nmessage\\\nabout a thing\n"'],
        {"a": "a long\nmessage\\\nabout a thing\n"},
    ),
    (
        'a="multiline\nmessage1\\\n" b="multiline\nmessage2\\\n"',
        ['a="multiline\nmessage1\\\n"', 'b="multiline\nmessage2\\\n"'],
        {"a": "multiline\nmessage1\\\n", "b": "multiline\nmessage2\\\n"},
    ),
    ('a="café eñyei"', ['a="café eñyei"'], {"a": "café eñyei"}),
    ("a=café b=eñyei", ["a=café", "b=eñyei"], {"a": "café", "b": "eñyei"}),
)

# Data for each tests. First input for both the data
SPLIT_ARGS = tuple((test[0], test[1]) for test in SPLIT_DATA)
PARSE_KV = tuple((test[0], test[2]) for test in SPLIT_DATA)


@pytest.mark.parametrize(
    "args, expected", SPLIT_ARGS, ids=[str(arg[0]) for arg in SPLIT_ARGS]
)
def test_split_args(args, expected):
    """Check that mulitple command line arguments are split into a list of args"""
    assert split_args(args) == expected


@pytest.mark.parametrize(
    "args, expected", PARSE_KV, ids=[str(arg[0]) for arg in PARSE_KV]
)
def test_parse_kv(args, expected):
    """
    Parse key value command line arguments and check that we get
    a correct python object
    """
    assert parse_key_value(args) == expected
