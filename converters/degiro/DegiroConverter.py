import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Dict

from Money import Money
from TaxRecord import TaxRecord
from converters.Converter import Converter
from currency.CurrencyConverter import CurrencyConverter


class NoISINError(BaseException):
    pass


class DegiroConverter(Converter):

    DEGIRO_DATE_FORMAT = '%d-%m-%Y'

    DATE_COLUMN_KEY = 'Date'
    PRODUCT_COLUMN_KEY = 'Product'
    ISIN_COLUMN_KEY = 'ISIN'
    QUANTITY_COLUMN_KEY = 'Quantity'

    VALUE_COLUMN_KEY = 'Price'
    VALUE_CURRENCY_COLUMN_KEY = 'Price currency'

    FEE_COLUMN_KEY = 'Transaction and/or third'
    FEE_CURRENCY_COLUMN_KEY = 'Transaction and/or third currency'

    def convert(self) -> List[TaxRecord]:
        if len(self.data) == 0:
            return []

        tax_report = []
        for record in self.data:
            try:
                date = self.__get_date(record)
                asset = self.__get_asset(record)
                quantity = self.__get_quantity(record)
                price = CurrencyConverter(self.__get_price(record)).convert_to_gbp(date).amount
                fee = CurrencyConverter(self.__get_fee(record)).convert_to_gbp(date).amount
                tax_report.append(TaxRecord(date, asset, quantity, price, fee))
            except NoISINError:
                logging.warning("Ignoring record as no ISIN found: {}".format(record))

        return tax_report

    def __get_date(self, data: Dict[str, str]) -> datetime:
        degiro_date_str: str = data[DegiroConverter.DATE_COLUMN_KEY]
        return datetime.strptime(degiro_date_str, DegiroConverter.DEGIRO_DATE_FORMAT)

    def __get_asset(self, data: Dict[str, str]) -> str:
        isin = data[DegiroConverter.ISIN_COLUMN_KEY]
        if not isin:
            raise NoISINError('No ISIN Error')

        return '{product} (ISIN: {isin})'.format(
            product=data[DegiroConverter.PRODUCT_COLUMN_KEY],
            isin=data[DegiroConverter.ISIN_COLUMN_KEY]
        )

    def __get_quantity(self, data: Dict[str, str]) -> Decimal:
        return Decimal(data[DegiroConverter.QUANTITY_COLUMN_KEY])

    def __get_price(self, data: Dict[str, str]) -> Money:
        return Money(
            abs(Decimal(data[DegiroConverter.VALUE_COLUMN_KEY])),
            data[DegiroConverter.VALUE_CURRENCY_COLUMN_KEY],
        )

    def __get_fee(self, data: Dict[str, str]) -> Money:
        value = data[DegiroConverter.FEE_COLUMN_KEY]
        if not value:
            return Money.zero()

        return Money(
            abs(Decimal(data[DegiroConverter.FEE_COLUMN_KEY])),
            data[DegiroConverter.FEE_CURRENCY_COLUMN_KEY],
        )