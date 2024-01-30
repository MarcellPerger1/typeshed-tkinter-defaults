from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from utils import readfile_json, writefile_json

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
    concise = _make_data_concise(merged)
    print('Writing concise file')
    writefile_json(OUT_DIR / 'concise.json', concise)


def _make_data_concise(merged_data: dict[str, dict[str, T]]) -> dict[str, dict[str, T]]:
    return {
        name: {
            k: (v[0] if _is_different_values(v) else v) for k, v in w_defaults.items()
        } for name, w_defaults in merged_data.items()}


def _is_different_values(v: object) -> bool:
    return (isinstance(v, (list, tuple))
            and len(v) == 2  # ['@different:n', [v0, v1, ...]]
            and isinstance(v[0], str)
            and isinstance(v[1], (list, tuple))
            and len(v[1]) >= 2
            and v[0].startswith('@different:'))


def merge_data(*data_ls: dict[str, dict[str, T]]) -> dict[str, dict[str, T]]:
    all_names = _union_keys(*data_ls)
    return {name: merge_widget(*_get_values(data_ls, name)) for name in all_names}


def _union_keys(*dicts: dict[T, U]) -> set[T]:
    return {k for d in dicts for k in d}


def merge_widget(*data_ls: dict[str, T]) -> dict[str, T]:
    all_keys = _union_keys(*data_ls)
    return {k: merge_attr(*_get_values(data_ls, k)) for k in all_keys}


def _get_values(data_ls: tuple[dict[str, T], ...], k: str) -> list[T]:
    sentinel = object()
    return [v for d in data_ls if (v := d.get(k, sentinel)) is not sentinel]


def merge_attr(*values: T) -> T:
    assert values
    try:
        nodup = _remove_dup_hashable(values)
    except TypeVar:
        nodup = _remove_dup_no_hash(values)
    first, *rest = nodup
    if not rest:
        return first
    return [f'@different:{len(nodup)}', nodup]


def _remove_dup_hashable(values: tuple[T, ...]) -> list[T]:
    return [*{*values}]


def _remove_dup_no_hash(values: tuple[T, ...]) -> list[T]:
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
