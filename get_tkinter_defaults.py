import json
import sys
import tkinter
import _tkinter as tk_internal
import inspect
from typing import TextIO

DEBUG = 1


def debug(msg: str, always=False, level=1):
    if DEBUG >= level or always:
        print(msg)


def short_repr(obj: object, max_len=40) -> str:
    try:
        value = repr(obj)
    except (TypeError, ValueError, NotImplementedError, AttributeError) as e:
        print(f'Exception ignored in __repr__: {type(e).__qualname__}: {e!s}',
              file=sys.stderr)
        return '<Error-in-repr>'
    if len(value) <= max_len:
        return value
    return value[:max_len - 3] + '...'


def get_defaults():
    out = {}
    temp_root = tkinter.Tk()
    for name in dir(tkinter):
        if name.startswith('_'):
            debug(f'SKIP key {name!r}: private name', level=2)
            continue
        if (value := getattr(tkinter, name, None)) is None:
            debug(f'SKIP key {name!r}: not present or None')
            continue
        if not inspect.isclass(value):
            debug(f'SKIP key {name!r} (type={short_repr(value)}): not a class', level=2)
            continue
        try:
            inst = value(temp_root)
        except (
                NotImplementedError, ValueError, TypeError, AttributeError,
                tkinter.TclError) as e:
            if isinstance(e, tkinter.TclError):
                print(f'TclError in 1-arg __init__: _tkinter.TclError: {e!s}',
                      file=sys.stderr)
            debug(f'INFO key {name!r}: no 1-arg __init__')
            try:
                inst = value()
            except (NotImplementedError, ValueError, TypeError, AttributeError):
                debug(f'SKIP key {name!r}: '
                      f'no 0-arg or 1-arg __init__')
                continue
        try:
            defaults = dict(inst)
        except (NotImplementedError, TypeError, ValueError, AttributeError):
            debug(f'INFO key {name!r} '
                  f'(inst={short_repr(inst)}): cannot convert to dict')
            # try another way
            try:
                options_list = inst.configure()
            except (NotImplementedError, TypeError, ValueError, AttributeError):
                debug(f'SKIP key {name!r} (inst={short_repr(inst)}): '
                      f'cannot configure 0-arg')
                continue
            try:
                defaults = {((tup[0], tup[1]) if tup[0] != tup[1] else tup[0]):
                            tup[4] for tup in options_list}
            except (NotImplementedError, TypeError, ValueError, AttributeError):
                debug(f'SKIP key {name!r} ('
                      f'inst={short_repr(inst)}): bad configure() output')
                continue
        debug(f'Success key {name!r} (type={short_repr(value)}, '
              f'inst={short_repr(inst)}): defaults={short_repr(defaults, 40)}')
        out[name] = defaults
    temp_root.destroy()
    return out


ALLOWED_JSON_TYPES = (int, float, str, dict, list, tuple, bool, type(None))


def make_value_serializable(v: object):
    if isinstance(v, ALLOWED_JSON_TYPES):
        return v
    if isinstance(v, tk_internal.Tcl_Obj):
        return f'@Tcl_Obj: type={v.typename}, value={v.string}'
    return f'@repr:{repr(v)}'


def transform_to_serializable(defaults_o: dict[str, dict]):
    def tform_one(o: dict[str, object]) -> dict[str, object]:
        return {key: make_value_serializable(value) for key, value in o.items()}

    return {key: tform_one(value) for key, value in defaults_o.items()}


def defaults_str(defaults: dict[str, dict] = None):
    if defaults is None:
        defaults = get_defaults()
    defaults_safe = transform_to_serializable(defaults)
    return json.dumps(defaults_safe, indent=4, sort_keys=True)


def write_defaults(file: TextIO, defaults: dict[str, dict] = None):
    if defaults is None:
        defaults = get_defaults()
    defaults_safe = transform_to_serializable(defaults)
    json.dump(defaults_safe, file, indent=4, sort_keys=True)
    return defaults
