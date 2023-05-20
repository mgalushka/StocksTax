import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Degiro transactions converter',
        description='Converts SVC degiro transactions file into pycryptax format',
        epilog='',
    )

    parser.add_argument('-f', '--filepath')


