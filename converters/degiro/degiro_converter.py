import argparse

from File import File
from degiro.DegiroConverter import DegiroConverter

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Degiro transactions converter',
        description='Converts CSV degiro transactions file into pycryptax format',
        epilog='',
    )

    parser.add_argument('-f', '--filepath')

    args = parser.parse_args()

    converter = DegiroConverter(File(args.filepath).get_io())
    report = converter.convert()

    with open('./examples/gains/real-2022-23.csv', 'w') as output:
        output.write('DATE,ASSET,AMOUNT,PRICE,FEE\n')
        for record in report:
            output.write(str(record) + '\n')
