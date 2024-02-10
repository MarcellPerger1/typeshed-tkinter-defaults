from __future__ import annotations

import inspect
import json
import os
import sys
import tkinter
import _tkinter as tk_internal
import tkinter.ttk as ttk
from tkinter import TclError
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


def get_temp_root():
    do_fallback = os.getenv('TK_DEFAULTS_FALLBACK', '0')
    if do_fallback.strip().lower() not in ('1', 'yes', 'true'):
        return tkinter.Tk()
    try:
        return tkinter.Tk()
    except TclError as e:
        debug(f'##[warn]WARN: Cannot initialize tkinter.Tk(): {e!s}')
        print(f'TclError in tkinter.Tk() constructor: {e!s}')
        # check if stuff works without a tk.Tk() instance
        tkinter.ttk.Button()
        return None


def get_defaults():
    out = {}
    temp_root = get_temp_root()
    for name in dir(ttk):
        if name.startswith('_'):
            debug(f'SKIP key {name!r}: private name', level=2)
            continue
        if (value := getattr(ttk, name, None)) is None:
            debug(f'SKIP key {name!r}: not present or None')
            continue
        if not inspect.isclass(value):
            debug(f'SKIP key {name!r} (type={short_repr(value)}): not a class', level=2)
            continue
        inst = None
        inst = _try_construct_option_menu(name, value, temp_root) if inst is None else inst
        inst = _construct_inst(name, value, temp_root) if inst is None else inst
        if inst is None:
            continue
        if (defaults := _get_inst_defaults(inst, name, value, temp_root)) is None:
            continue
        debug(f'Success key {name!r} (type={short_repr(value)}, '
              f'inst={short_repr(inst)}): defaults={short_repr(defaults, 40)}')
        out['ttk.' + name] = defaults
    if temp_root is not None:
        temp_root.destroy()
    return out


def _get_inst_defaults(inst, name: str, _cls, _temp_root: tkinter.Tk | None) -> dict[str, ...] | None:
    try:
        # Stringify all the values so that tkinter knows that it needs to
        # calculate the string value but tkinter doesn't actually return
        # the string value the first time for some reason so we need
        # to call it again after it has calculated the string value
        _ = str(dict(inst))
        return dict(inst)
    except (NotImplementedError, TypeError, ValueError, AttributeError):
        debug(f'INFO key {name!r} (inst={short_repr(inst)}): cannot convert to dict')
    # try another way
    try:
        _ = str(inst.configure())
        options_list = inst.configure()
    except (NotImplementedError, TypeError, ValueError, AttributeError):
        debug(f'SKIP key {name!r} (inst={short_repr(inst)}): '
              f'cannot configure 0-arg')
        return None
    try:
        return {((tup[0], tup[1]) if tup[0] != tup[1] else tup[0]):
                tup[4] for tup in options_list}
    except (NotImplementedError, TypeError, ValueError, AttributeError):
        debug(f'SKIP key {name!r} ('
              f'inst={short_repr(inst)}): bad configure() output')
        return None


def _construct_inst(name: str, value, temp_root: tkinter.Tk | None):
    try:
        inst = value(temp_root)
    except (
            NotImplementedError, ValueError, TypeError, AttributeError,
            TclError, RuntimeError) as e:
        if isinstance(e, (TclError, RuntimeError)):
            print(f'TclError in 1-arg __init__: _tkinter.TclError: {e!s}',
                  file=sys.stderr)
        debug(f'INFO key {name!r}: no 1-arg __init__')
        try:
            inst = value()
        except (NotImplementedError, ValueError, TypeError, AttributeError, RuntimeError):
            if isinstance(e, (TclError, RuntimeError)):
                print(f'TclError in 0-arg __init__: _tkinter.TclError: {e!s}',
                      file=sys.stderr)
            debug(f'SKIP key {name!r}: no 0-arg or 1-arg __init__')
            return None
    return inst


def _try_construct_option_menu(name: str, value: type[ttk.OptionMenu],
                               temp_root: tkinter.Tk | None):
    if name != 'OptionMenu':
        return None
    temp_var = tkinter.Variable(temp_root)
    try:
        om = value(temp_root, temp_var)
    except (NotImplementedError, ValueError, TypeError, AttributeError,
            TclError, RuntimeError) as e:
        if isinstance(e, (TclError, RuntimeError)):
            print(f'Error in 2-arg OptionMenu.__init__: '
                  f'{type(e).__name__}: {e!s}', file=sys.stderr)
        debug(f"INFO key 'OptionMenu' (special): no 2-arg __init__(master=root)")
        try:
            om = value(None, temp_var)
        except (NotImplementedError, ValueError, TypeError, AttributeError,
                TclError, RuntimeError) as e:
            if isinstance(e, (TclError, RuntimeError)):
                print(f'Error in 2-arg __init__ (with master=None): '
                      f'{type(e).__name__}: {e!s}', file=sys.stderr)
            debug(f"WARN key 'OptionMenu' (special): no 2-arg __init__ at all")
            return None
    return om


ALLOWED_JSON_TYPES = (int, float, str, dict, list, tuple, bool, type(None))


def make_value_serializable(v: object):
    if isinstance(v, ALLOWED_JSON_TYPES):
        return v
    if isinstance(v, tk_internal.Tcl_Obj):
        return f'@Tcl_Obj: type={v.typename}, value={v.string}'
    return f'@repr:{repr(v)}'


class _TclSafeEncoder(json.JSONEncoder):
    def default(self, o: object):
        return make_value_serializable(o)


def transform_to_serializable(defaults_o: dict[str, dict]):
    def tform_one(o: dict[str, object]) -> dict[str, object]:
        return {key: make_value_serializable(value) for key, value in o.items()}

    return {key: tform_one(value) for key, value in defaults_o.items()}


def defaults_str(defaults: dict[str, dict] = None):
    if defaults is None:
        defaults = get_defaults()
    defaults_safe = transform_to_serializable(defaults)
    return json.dumps(defaults_safe, indent=4, sort_keys=True, cls=_TclSafeEncoder)


def write_defaults(file: TextIO, defaults: dict[str, dict] = None):
    if defaults is None:
        defaults = get_defaults()
    defaults_safe = transform_to_serializable(defaults)
    json.dump(defaults_safe, file, indent=4, sort_keys=True, cls=_TclSafeEncoder)
    return defaults


if __name__ == '__main__':
    print(defaults_str())
