from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from EquityAction import EquityAction
from Money import Money
from TaxRecord import TaxRecord


@dataclass
class DetailedTaxRecord:
    date: datetime
    asset_name: str
    amount: Decimal
    operation: EquityAction

    price: Money
    price_conversion_rate: Decimal
    price_gbp: Decimal

    fee: Money
    fee_conversion_rate: Decimal
    fee_gbp: Decimal

    @staticmethod
    def header():
        return 'DATE,ASSET,OPERATION,AMOUNT,PRICE,PRICE_CURRENCY,PRICE_CONVERSION_RATE,PRICE_GBP,TOTAL_COST_GBP,' \
               'FEE,FEE_CURRENCY,FEE_CONVERSION_RATE,FEE_GBP\n'

    def __str__(self):
        return '{date},{asset},{operation},{amount:.0f},' \
               '{price:.2f},{price_currency},{price_conversion_rate:.4f},{price_gbp:.2f},{total_cost_gbp:.2f},' \
               '{fee:.2f},{fee_currency},{fee_conversion_rate:.4f},{fee_gbp:.2f}\n'.format(
            date=self.date.strftime(TaxRecord.TAX_RECORD_DATE_FORMAT),
            asset=self.asset_name,
            operation=self.operation.value,
            amount=self.amount,
            price=self.price.amount,
            price_currency=self.price.currency,
            price_conversion_rate=self.price_conversion_rate,
            price_gbp=self.price_gbp,
            total_cost_gbp=self.amount * self.price_gbp,
            fee=self.fee.amount,
            fee_currency=self.fee.currency,
            fee_conversion_rate=self.fee_conversion_rate,
            fee_gbp=self.fee_gbp,
        )