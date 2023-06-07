import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict

@dataclass
class Split:
    date: datetime
    multiplier: Decimal

class StockSplit:

    SPLITS: Dict[str, Split] = {
        'GOOGL': Split(datetime.strptime('2022-07-15', '%Y-%m-%d'), Decimal(20))
    }

    def __init__(self, index: str, quantity: Decimal, price: Decimal, date: datetime):
        self.index = index
        self.raw_quantity = quantity
        self.raw_price = price
        self.date = date

    def quantity(self):
        if self.index in StockSplit.SPLITS:
            split = StockSplit.SPLITS[self.index]
            if self.date <= split.date:
                result_quantity = self.raw_quantity * split.multiplier
                logging.debug('Applying stock split to {index}; Quantity changed from {original:.2f} to {to:.2f}'.format(
                    index=self.index,
                    original=self.raw_quantity,
                    to=result_quantity,
                ))
                return result_quantity
        return self.raw_quantity

    def price(self):
        if self.index in StockSplit.SPLITS:
            split = StockSplit.SPLITS[self.index]
            if self.date <= split.date:
                result_price = self.raw_price / split.multiplier
                logging.debug('Applying stock split to {index}; Price changed from {original:.2f} to {to:.2f}'.format(
                    index=self.index,
                    original=self.raw_price,
                    to=result_price,
                ))
                return result_price
        return self.raw_price