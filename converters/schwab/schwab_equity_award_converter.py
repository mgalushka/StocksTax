import argparse
import logging

from File import File
from schwab.SchwabEquityAwardConverter import SchwabEquityAwardConverter

'''
To use: 
(1) Go to https://client.schwab.com/app/accounts/transactionhistory/#/
(2) Select Equity Award Center and appropriate period
(3) Export to CSV
'''
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Schwab Equity Award transactions converter',
        description='Converts CSV Schwab Equity Award transactions file into pycryptax format',
        epilog='',
    )

    parser.add_argument('-f', '--filepath')

    args = parser.parse_args()

    converter = SchwabEquityAwardConverter(File(args.filepath).get_io())
    report = converter.convert()

    for r in report:
        logging.warning(r)

    with open('./examples/gains/real-schwab-equity-2022-23.csv', 'w') as output:
        output.write('DATE,ASSET,AMOUNT,PRICE,FEE\n')
        for record in report:
            output.write(str(record) + '\n')
