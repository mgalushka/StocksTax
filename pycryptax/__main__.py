# Copyright 2019 Matthew Mitchell

import argparse, sys, logging
from contextlib import contextmanager
from pycryptax import csvdata, prices, gains, util

GAINS_DIR = "/gains"
PRICES_DIR = "/prices"
ERR_NOTICE = """

Please read the README.md and see the ./examples directory for an example \
working directory
"""

BEFORE_MSG = """
Do not rely on this software for accuracy. Anything provided by this software
does not constitute advice in any form. The software is provided "as is",
without warranty of any kind. Please see the LICENSE and README.md files.
\n\n

Transaction matching report
"""

def fail(message):
    print("\n" + message + ERR_NOTICE, file=sys.stderr)
    sys.exit(1)

@contextmanager
def csvErrorHandler(what, directory, reportAsset):

    try:
        yield
    except FileNotFoundError:
        fail(
            "You need to provide {} in the {} directory".format(what, directory)
        )
    except csvdata.CSVNotOpenable as e:
        fail("Cannot open CSV file {}".format(str(e)))
    except csvdata.CSVKeyError as e:
        fail("Missing column(s) for {}".format(e.filename))
    except csvdata.CSVDateError as e:
        fail(
"Incorrect date \"{}\" in {} on line {}. An example date is 2020-01-05"
            .format(e.date, e.filename, e.line)
        )
    except csvdata.CSVNumberError as e:
        fail(
"A non numeric value found in {} on line {} where a number is expected"
            .format(e.filename, e.line)
        )
    except prices.AssetPricesNotFound as e:
        fail("""\
Cannot find a {1} price for {0}. Please provide a {0}_{1}.csv file in the \
prices directory""".format(e.asset, reportAsset))
    except prices.PriceNotFoundForDate as e:
        fail(
            "Cannot find a {} price for {}"
            .format(e.asset, util.getPrettyDate(e.date))
        )

def main():

    # Arguments

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Calculate UK Income and Capital Gain for Tax. Uses Section 104 holding rules and
30-day bed and breakfasting rules. Automatically converts asset amounts into a
specified reporting asset given price data.\
        """,
        epilog="""\
Use the 'income' command to produce a summary of revenue and
expenses.

Use the 'txs' command to output income calculations for each
transaction to CSV, containing the original asset amount, the price
and the reporting asset amount.

Use the 'gain' command to produce a summary of asset gains and
losses, and a summary of current section 104 holdings.

Use the 'disposals' command to output a list of asset disposal
information to CSV.
        """
    )

    parser.add_argument(
        "action", choices=["gain"]
    )
    parser.add_argument("start", type=str, help="Starting date of calculation")
    parser.add_argument("end", type=str, help="End date of calculation")
    parser.add_argument(
        "--reportingcurrency", "-c", type=str, default="gbp",
        help="The reporting currency (default \"gbp\") to present calculations"
    )
    parser.add_argument(
        "--dir", "-d", type=str, default="./",
        help="The root directory of the CSV data (default \"./\")"
    )

    args = parser.parse_args()

    reportAsset = args.reportingcurrency
    action = args.action
    rootDir = args.dir
    start = util.dateFromString(args.start)
    end = util.dateFromString(args.end)

    logging.warning('Generating report from: {} to {}'.format(start, end))

    def getCGCalc(**kwargs):
        with csvErrorHandler(
            "capital gains information", rootDir + GAINS_DIR, reportAsset
        ):
            return gains.CapitalGainCalculator(
                csvdata.CSVTransactionGains(rootDir + GAINS_DIR), start, end,
                **kwargs
            )

    if action == "gain":
        print(BEFORE_MSG)
        summary = getCGCalc(summary=True).printSummary()
        print(summary)

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    main()
