import argparse
import logging

from File import File
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

    converter = SchwabTransactionsConverter(File(args.filepath).get_io())
    report = converter.convert()

    for r in report:
        logging.warning(r)

    with open('./examples/gains/real-schwab-transactions-2022-23.csv', 'w') as output:
        output.write('DATE,ASSET,AMOUNT,PRICE,FEE\n')
        for record in report:
            output.write(str(record) + '\n')
