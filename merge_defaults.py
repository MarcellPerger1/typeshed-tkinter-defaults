from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar, Iterable

from utils import readfile_json, writefile_json, JsonT

DEFAULTS_DIR = Path("./tkinter_defaults")
OUT_DIR = Path('./merged_defaults')

T = TypeVar('T')
U = TypeVar('U')


def _read_defaults():
    out = {}
    for f in DEFAULTS_DIR.iterdir():
        if not f.is_file():
            continue
        data = readfile_json(f)
        out[f.name] = data
    return out


def merge_defaults():
    OUT_DIR.mkdir(exist_ok=True)
    merged = merge_data(*_read_defaults().values())
    print('Writing detailed file')
    writefile_json(OUT_DIR / 'details.json', merged)
    concise = summarise_data_1(merged)
    print('Writing concise file')
    writefile_json(OUT_DIR / 'concise.json', concise)
    concise_2 = summarize_data_2(merged)
    print('Writing extra concise file')
    writefile_json(OUT_DIR / 'concise_2.json', concise_2)


def summarize_data_2(merged_data: dict[str, dict[str, JsonT]]) -> dict[str, dict[str, str]]:
    return {
        name: {
            k: _summarize_w_val_2(v) for k, v in w_defaults.items()
            if not _is_different_values(v)
        } for name, w_defaults in merged_data.items()}


def _summarize_w_val_2(v: T) -> T | str | None:
    assert not _is_different_values(v), "different values should've been filtered out"
    if _is_type_diff(v):
        return f'{v[1]}    @typeDiff'
    return v


def summarise_data_1(merged_data: dict[str, dict[str, T]]) -> dict[str, dict[str, T]]:
    return {
        name: {
            k: _summarise_w_val(v) for k, v in w_defaults.items()
        } for name, w_defaults in merged_data.items()}


def _summarise_w_val(v):
    if _is_different_values(v):
        return v[0]  # '@different:n'
    if _is_type_diff(v):
        return f'{v[0]} = {v[1]}'
    return v


def _is_type_diff(v: object) -> bool:
    return (isinstance(v, (list, tuple))
            and len(v) == 3  # ['@typeDiff:n', value, [v0, v1, ..., vn]]
            and isinstance(v[0], str)
            and isinstance(v[2], (list, tuple))
            and len(v[2]) >= 2
            and v[0].startswith('@typeDiff'))


def _is_different_values(v: object) -> bool:
    return (isinstance(v, (list, tuple))
            and len(v) == 2  # ['@different:n', [v0, v1, ...]]
            and isinstance(v[0], str)
            and isinstance(v[1], (list, tuple))
            and len(v[1]) >= 2
            and v[0].startswith('@different:'))


def merge_data(*data_ls: dict[str, dict[str, T]]) -> dict[str, dict[str, JsonT]]:
    all_names = _union_keys(*data_ls)
    return {name: merge_widget(*_get_values(data_ls, name)) for name in all_names}


def _union_keys(*dicts: dict[T, U]) -> set[T]:
    return {k for d in dicts for k in d}


def merge_widget(*data_ls: dict[str, T]) -> dict[str, JsonT]:
    all_keys = _union_keys(*data_ls)
    return {k: merge_attr(*_get_values(data_ls, k)) for k in all_keys}


def _get_values(data_ls: tuple[dict[str, T], ...], k: str) -> list[T]:
    sentinel = object()
    return [v for d in data_ls if (v := d.get(k, sentinel)) is not sentinel]


def merge_attr(*values: T) -> JsonT:
    all_eq, val = _get_all_strict_equal(values)
    if all_eq:
        return val
    if (ret_loose_eq := _merge_loose_eq_values(values)) is not None:
        return ret_loose_eq
    return _merge_different_vals(values)


def _merge_loose_eq_values(values: tuple[T, ...]) -> JsonT | None:
    """Sorts all options for consistent output,
    only return None if not loose eq"""
    data = [_get_obj_data(d) for d in values]
    all_val_eq, val = _get_all_loose_eq(data)
    if not all_val_eq:
        return None
    data_no_dup = _remove_dup_obj_data(data)
    return [f'@typeDiff:{len(data_no_dup)}', val,
            # sorted() can't error as its all strings so no try/except
            sorted([d.typ for d in data_no_dup])]


def _merge_different_vals(values: tuple[T, ...]) -> JsonT:
    """Sorts all options for consistent output"""
    # Here, just write the raw values - they're probably more useful
    values_no_dup = _remove_dup(values)
    try:
        values_no_dup.sort()
    except TypeError:
        values_no_dup.sort(key=str)  # fallback for unsortable values
    return [f'@different:{len(values_no_dup)}', values_no_dup]


def _get_all_strict_equal(values: tuple[T, ...]) -> tuple[bool, T | None]:
    assert values
    first, *rest = _remove_dup(values)
    if not rest:
        return True, first
    return False, None


def _get_all_loose_eq(data: list[ObjData]) -> tuple[bool, str]:
    """Returns tuple (isLooseEq, value?)"""
    values = [d.value for d in data]
    return _get_all_strict_equal(tuple(values))


def _remove_dup_obj_data(data: Iterable[ObjData]) -> list[ObjData]:
    return [*{*data}]


@dataclass(frozen=True)
class ObjData:
    typ: str
    value: str


TCL_OBJ_RE_C = re.compile(r'''^@Tcl_Obj: type=(.*), value=(.*)$''')


def _get_obj_data(o: JsonT) -> ObjData:
    if isinstance(o, str):
        if o.startswith('@Tcl_Obj:'):
            return _get_tcl_obj_data(o)
        return ObjData('@Py_str', o)
    if isinstance(o, int):
        return ObjData('@Py_int', str(o))
    if o is None:
        return ObjData('@Py_None', 'None')
    if isinstance(o, float):
        if o.is_integer():
            return ObjData('@Py_float', str(int(o)))
        return ObjData('@Py_float', str(o))
    if isinstance(o, bool):
        return ObjData('@Py_bool', str(o))
    return ObjData(f'@Py_{type(o).__name__}', str(o))


def _get_tcl_obj_data(s: str) -> ObjData:
    m = TCL_OBJ_RE_C.match(s)
    assert m is not None
    typ, value = m.groups()
    return ObjData(typ, value)


def _remove_dup(values: Iterable[T]) -> list[T]:
    try:
        return _remove_dup_hashable(values)
    except (TypeError, NotImplementedError):
        return _remove_dup_no_hash(values)


def _remove_dup_hashable(values: Iterable[T]) -> list[T]:
    return [*{*values}]


def _remove_dup_no_hash(values: Iterable[T]) -> list[T]:
    # This is a bit of a hack as we exploit the fact that dict removes duplicates
    #  but we need to make the keys hashable (so transform them to immutable)
    return [*{_copy_as_hashable(v): v for v in values}.values()]


def _copy_as_hashable(value):
    # I would like to use match here but need as much compatibility as we can get
    try:
        hash(value)
    except TypeError:
        pass
    else:
        return value
    if isinstance(value, list):
        return (*value,)  # as tuple
    elif isinstance(value, set):
        return frozenset(value)
    elif isinstance(value, dict):
        return _HashableDict(value)
    raise TypeError(f"Can't convert {type(value).__name__} to immutable")


class _HashableDict(dict):
    __slots__ = ('_hash',)

    def _err_immut(self, *_args, **_kwargs):
        raise NotImplementedError("_HashableDict is immutable")

    __setitem__ = _err_immut
    update = _err_immut
    setdefault = _err_immut
    popitem = _err_immut
    pop = _err_immut
    clear = _err_immut

    def __hash__(self):
        try:
            return self._hash
        except AttributeError:
            self._hash = hash(frozenset(self.items()))
        return self._hash


def main():
    merge_defaults()


if __name__ == '__main__':
    main()
