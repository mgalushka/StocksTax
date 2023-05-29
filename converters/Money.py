from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Money:
    amount: Decimal
    currency: str

    @staticmethod
    def zero():
        return Money(Decimal(0), 'GBP')

    def __str__(self):
        return '{currency} {amount:.4f}'.format(
            currency=self.currency,
            amount=self.amount,
        )
