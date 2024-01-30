from __future__ import annotations

import json
from os import PathLike
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import TypeAlias


def _assert_not_write(mode: str):
    """This function exists to prevent us accidentally truncating a file
    that we wanted to read from (but accidentally specified mode=w) as it would
    be bad if we truncate and then raise error on attempt to read
    (or even worse: silently return nothing if w+)
    - we should raise error BEFORE open/truncate"""
    assert set('wxa').isdisjoint(set(mode))


def readfile(path: str | PathLike, mode='r') -> str:
    _assert_not_write(mode)
    with open(path, mode, encoding='utf8') as f:
        return f.read()


def writefile(path: str | PathLike, content: str, mode='w'):
    with open(path, mode, encoding='utf8') as f:
        f.write(content)


JsonT: TypeAlias = 'None | bool | float | int | str | list[JsonT] | dict[str, JsonT]'


def readfile_json(path: str | PathLike, mode='r') -> JsonT:
    _assert_not_write(mode)
    with open(path, mode, encoding='utf8') as f:
        return json.load(f)


def writefile_json(path: str | PathLike, content: JsonT | Any, mode='w'):
    with open(path, mode, encoding='utf8') as f:
        json.dump(content, f, sort_keys=True)
