# typeshed-tkinter-defaults
Small script for finding default options of tkinter widgets

## How to contribute data for the defaults
1. Fork and clone this repository
2. Run `python -m workflow_local`
3. Commit the files added/modiified by the script
4. Push to your fork
5. Create a pull request

## The output
The merged output is in [`merged_defaults/`](./merged_defaults):
- [`details.json`](./merged_defaults/details.json) will give you all the values on all the different platforms and all the types for `Tcl_Obj` objects
- [`concise.json`](./merged_defaults/concise.json) will tell you if something is the same on all platforms or only types differ (and will give you the value) and will tell you if a key is different (and doesn't list out all values)
- [`concise_2.json`](./merged_defaults/concise_2.json) will only show the ones where the value is the same (it will omit any differing ones)
