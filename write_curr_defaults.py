from __future__ import annotations

import platform
from os import PathLike
from pathlib import Path

from get_tkinter_defaults import defaults_str


DEBUG = 1


def debug(msg: str, always=False, level=1):
    if DEBUG >= level or always:
        print(msg)


def _writefile(path: str | PathLike, content: str, mode='w'):
    with open(path, mode) as f:
        f.write(content)


def _readfile(path: str | PathLike, mode='r') -> str:
    assert 'w' not in mode
    with open(path, mode) as f:
        return f.read()


def get_arch_key():
    return platform.platform()


OUT_PATH_FMT = 'tkinter_defaults/default{n}__{plat}.json'


def _find_available_path(result: str, check_overwrite=True):
    """Return an available path to write to (or None if no write needed)"""
    def get_out_path():
        return Path(OUT_PATH_FMT.format(n=n, plat=plat))

    plat = get_arch_key()
    n = 0
    out_path = get_out_path()
    if not check_overwrite:
        return out_path
    while n < 1_000:
        if not out_path.exists():
            return out_path  # free path, write here
        orig = _readfile(out_path)
        if orig == result:
            return None  # same result so no write
        n += 1
        out_path = get_out_path()
    raise TimeoutError("Checked 1000 paths, none available. "
                       "Exiting to avoid excessive CPU/disk consumption. "
                       "(should never be THIS many of a single platform)")


def run(check_overwrite=True):
    defaults_s = defaults_str()
    debug('INFO: Writing defaults locally')
    _writefile('tkinter_defaults_curr.json', defaults_s)
    out_path = _find_available_path(defaults_s, check_overwrite)
    if out_path is not None:
        _writefile(out_path, defaults_s)
        debug('INFO: Writing defaults to tkinter_defaults/')
    else:
        debug('INFO: No write to tkinter_defaults/ needed (same as existing info)')


if __name__ == '__main__':
    run()
