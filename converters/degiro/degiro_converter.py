import argparse
from io import StringIO

from DetailedTaxRecord import DetailedTaxRecord
from File import File
from TaxRecord import TaxRecord
from degiro.DegiroConverter import DegiroConverter

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Degiro transactions converter',
        description='Converts CSV degiro transactions file into pycryptax format',
        epilog='',
    )

    parser.add_argument('-f', '--filepath')

    args = parser.parse_args()

    log_io = StringIO()
    converter = DegiroConverter(File(args.filepath).get_io(), log_io)
    report = converter.convert()

    with open('./examples/logs/real-2022-23.log.csv', 'w') as log:
        log.write(DetailedTaxRecord.header())
        log.write(log_io.getvalue())

    with open('./examples/gains/real-2022-23.csv', 'w') as output:
        output.write(TaxRecord.header())
        for record in report:
            output.write(str(record) + '\n')
