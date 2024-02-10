import write_curr_defaults
import merge_defaults

from get_ttk_defaults import merge_ttk_defaults, write_curr_ttk_defaults


def main():
    print('Gathering and writing tkinter defaults...')
    write_curr_defaults.run()
    print('Merging tkinter defaults...')
    merge_defaults.main()
    print('Finished tkinter defaults.')
    print('Gathering and writing ttk defaults...')
    write_curr_ttk_defaults.run()
    print('Merging ttk defaults...')
    merge_ttk_defaults.main()
    print('Finished ttk defaults')
    print('Done, no errors!')


if __name__ == '__main__':
    main()
