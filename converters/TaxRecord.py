from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class TaxRecord:
    date: datetime
    asset_name: str
    amount: Decimal
    price_gbp: Decimal
    fee_gbp: Decimal

    TAX_RECORD_DATE_FORMAT = '%Y-%m-%d'

    def __str__(self):
        return '{date},{asset},{amount:.4g},{price:.4g},{fee:.4g}'.format(
            date=self.date.strftime(TaxRecord.TAX_RECORD_DATE_FORMAT),
            asset=self.asset_name,
            amount=self.amount,
            price=self.price_gbp,
            fee=self.fee_gbp,
        )