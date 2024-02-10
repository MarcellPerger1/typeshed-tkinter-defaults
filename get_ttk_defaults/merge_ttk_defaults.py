from __future__ import annotations

from pathlib import Path

from merge_defaults import merge_data, summarise_data_1, summarize_data_2
from utils import readfile_json, writefile_json

DEFAULTS_DIR = Path("./ttk_defaults")
OUT_DIR = Path('./ttk_merged_defaults')


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


def main():
    merge_defaults()


if __name__ == '__main__':
    main()
