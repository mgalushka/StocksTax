import csv, bisect, os
import logging
from decimal import Decimal, InvalidOperation
from pycryptax import util, datemap

class CSVNotOpenable(Exception):
    pass

class CSVKeyError(KeyError):
    def __init__(self, filename):
        self.filename = filename

class CSVDateError(ValueError):
    def __init__(self, filename, date, line):
        self.filename = filename
        self.date = date
        self.line = line

class CSVNumberError(ValueError):
    def __init__(self, filename, line):
        self.filename = filename
        self.line = line

def getDateFromRow(row):
    return util.dateFromString(row["DATE"])

def isEmpty(v):
    return not v or v.isspace()

class CSVDateMap(datemap.DateMap):

    def _processFile(self, filename):

        logging.warning('Processing file: {}'.format(filename))

        try:
            f = open(filename, newline='')
        except FileNotFoundError as e:
            raise e
        except (IOError, OSError) as e:
            raise CSVNotOpenable(str(e))

        with f:

            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)

            reader = csv.DictReader(f, dialect=dialect)

            for line, row in enumerate(reader):

                line += 2

                try:

                    if isEmpty(row["DATE"]):
                        continue

                    try:
                        date = getDateFromRow(row)
                    except ValueError:
                        raise CSVDateError(filename, row["DATE"], line)

                    data = self._processRow(row)
                    self.insert(date, data)

                except KeyError as e:
                    raise CSVKeyError(filename)
                except InvalidOperation as e:
                    raise CSVNumberError(filename, line)

    def __init__(self, path, requireDir=True):

        super().__init__()

        if os.path.isdir(path) != requireDir:
            raise FileNotFoundError

        if requireDir:
            for f in os.listdir(path):
                if f.endswith('.csv'):
                    self._processFile(path + "/" + f)
        else:
            self._processFile(path)

class IncomeTx():

    def __init__(self, asset, amount, note):
        self.asset = asset
        self.amount = Decimal(amount)
        self.note = note

class CSVIncome(CSVDateMap):

    def __init__(self, filename):
        super().__init__(filename)

    def _processRow(self, row):
        return IncomeTx(row["ASSET"], row["AMOUNT"], row.get("NOTE"))

class GainTx():

    def __init__(self, sellAsset, buyAsset, sellAmount, buyAmount):

        if not isEmpty(sellAsset):
            self.sellAsset = sellAsset
            self.sellAmount = Decimal(sellAmount)
        else:
            self.sellAsset = None
            self.sellAmount = None

        if not isEmpty(buyAsset):
            self.buyAsset = buyAsset
            self.buyAmount = Decimal(buyAmount)
        else:
            self.buyAsset = None
            self.buyAmount = None

class TransactionGainTx():

    def __init__(self, asset, amount, price, fee):

        if not isEmpty(asset):
            self.asset = asset
            self.amount = Decimal(amount)
            self.price = Decimal(price)
            self.fee = Decimal(fee)
        else:
            self.asset = None
            self.amount = None
            self.price = None
            self.fee = None

    def __str__(self):
        return '{buy_or_sell} {amount} {asset} @ £{price:0.2f} with fee of £{fee:0.2f}'.format(
            buy_or_sell='BUY' if self.amount >= 0 else 'SELL',
            amount=abs(self.amount),
            asset=self.asset,
            price=self.price,
            fee=self.fee,
        )

class CSVGains(CSVDateMap):

    def __init__(self, filename):
        super().__init__(filename)

    def _processRow(self, row):
        return GainTx(
            row["SELL ASSET"], row["BUY ASSET"],
            row["SELL AMOUNT"], row["BUY AMOUNT"]
        )

class CSVTransactionGains(CSVDateMap):

    def __init__(self, filename, requireDir=True):
        super().__init__(filename, requireDir)

    def _processRow(self, row):
        return TransactionGainTx(
            row["ASSET"], row["AMOUNT"], row["PRICE"], row["FEE"]
        )

class CSVPrices(CSVDateMap):

    def __init__(self, filename, quoted):
        super().__init__(filename, False)
        self._quoted = quoted

    def _processRow(self, row):
        return Decimal(row["PRICE"])

    def quotedAsset(self):
        return self._quoted

    def __getitem__(self, ind):
        i = bisect.bisect(self._dates, ind) - 1
        if i < 0:
            raise KeyError
        return self._values[i]

