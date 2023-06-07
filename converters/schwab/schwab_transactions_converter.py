import argparse
from io import StringIO

from DetailedTaxRecord import DetailedTaxRecord
from File import File
from TaxRecord import TaxRecord
from schwab.SchwabTransactionsConverter import SchwabTransactionsConverter

'''
To use: 
(1) Go to https://client.schwab.com/app/accounts/transactionhistory/#/
(2) Select Individual and appropriate period
(4) Untick "Show Total"
(3) Export to CSV
'''
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Schwab transactions converter',
        description='Converts CSV Schwab transactions file into pycryptax format',
        epilog='',
    )

    parser.add_argument('-f', '--filepath')

    args = parser.parse_args()

    log_io = StringIO()
    converter = SchwabTransactionsConverter(File(args.filepath).get_io(), log_io)
    report = converter.convert()

    with open('./examples/logs/real-schwab-transactions-2022-23.log.csv', 'w') as log:
        log.write(DetailedTaxRecord.header())
        log.write(log_io.getvalue())

    with open('./examples/gains/real-schwab-transactions-2022-23.csv', 'w') as output:
        output.write(TaxRecord.header())
        for record in report:
            output.write(str(record) + '\n')
