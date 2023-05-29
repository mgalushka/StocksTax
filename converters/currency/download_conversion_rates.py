import logging
from datetime import datetime
from decimal import Decimal

from Money import Money
from currency.CurrencyConverter import CurrencyConverter

if __name__ == '__main__':
    converter = CurrencyConverter(Money(Decimal(11.5), 'USD'))
    logging.warning("Conversion rate is {}".format(converter.get_rate_to_gbp(datetime.now())))

    to_convert = Money(Decimal(11.5), 'USD')
    logging.warning("Conversion from {money} is {money2}".format(
        money=to_convert,
        money2=CurrencyConverter(to_convert).convert_to_gbp(datetime.now())
    ))

    to_convert = Money(Decimal(4500), 'GBX')
    logging.warning("Conversion from {money} is {money2}".format(
        money=to_convert,
        money2=CurrencyConverter(to_convert).convert_to_gbp(datetime.now())
    ))

    to_convert = Money(Decimal(33), 'GBP')
    logging.warning("Conversion from {money} is {money2}".format(
        money=to_convert,
        money2=CurrencyConverter(to_convert).convert_to_gbp(datetime.now())
    ))