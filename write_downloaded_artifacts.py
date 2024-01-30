from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

from utils import readfile_json, writefile_json, writefile, JsonT, readfile


ARTIFACTS_DIR = Path("./downloaded_artifacts")
DEFAULTS_OUT_DIR = Path('./tkinter_defaults')


def removesuffix(s: str, suffix: str) -> str:
    if sys.version_info >= (3, 9):
        return s.removesuffix(suffix)
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def get_artifacts() -> dict[str, JsonT]:
    out = {}
    for a_dir in ARTIFACTS_DIR.iterdir():
        assert a_dir.is_dir()
        name = readfile(a_dir / 'curr_out_filename.txt').strip()
        data = readfile_json(a_dir / 'tkinter_defaults_curr.json')
        out[name] = data
    return out


def write_artifact(name: str, data: JsonT):
    path = Path('.') / name
    if not path.exists():
        return writefile_json(path, data, mode='x')
    assert path.is_file()
    would_write = json.dumps(data)
    actual_data = readfile_json(data)
    if would_write == actual_data:
        return
    warnings.warn(RuntimeWarning(
        "Tried to write artifact to file that already exists and if different!"
        " This is a BUG in the write_curr_defaults.py! Dumping artifact."))
    _debug_dump_artifact(name, would_write)


def _debug_dump_artifact(name: str, data_s: str):
    # Don't really want to find a place to put it, duplicating the functionality
    # in write_curr_defaults (that was broken, causing this to be called)...
    # so just create some new functionality that could also break. ;-)
    dump_dir = DEFAULTS_OUT_DIR / 'error_dumps'
    dump_dir.mkdir(exist_ok=True)
    extra_h = hashlib.sha256(data_s.encode('utf8')).hexdigest()[:16]
    newfile = dump_dir / f'dump__{removesuffix(name, ".json")}__{extra_h}.json'
    writefile(newfile, data_s)


def write_artifacts():
    artifacts = get_artifacts()
    for name, data in artifacts.items():
        write_artifact(name, data)


def main():
    write_artifacts()


if __name__ == '__main__':
    main()
