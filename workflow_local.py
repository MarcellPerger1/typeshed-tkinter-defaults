import write_curr_defaults
import merge_defaults


def main():
    print('Gathering and writing defaults...')
    write_curr_defaults.run()
    print('Merging defaults...')
    merge_defaults.main()
    print('Done, no significant errors!')


if __name__ == '__main__':
    main()
