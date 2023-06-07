import logging
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import List, Dict, Optional

from Converter import Converter
from EquityAction import EquityAction
from IndexRenaming import IndexRenaming
from Money import Money
from StockSplit import StockSplit
from TaxRecord import TaxRecord
from currency.CurrencyConverter import CurrencyConverter


class SchwabTransactionsConverter(Converter):

    SCHWAB_DATE_FORMAT = '%m/%d/%Y'

    DATE_COLUMN_KEY = 'Date'
    ACTION_COLUMN_KEY = 'Action'
    PRODUCT_COLUMN_KEY = 'Symbol'
    DESCRIPTION_COLUMN_KEY = 'Description'
    QUANTITY_COLUMN_KEY = 'Quantity'
    PRICE_COLUMN_KEY = 'Price'
    FEES_COLUMN_KEY = 'Fees & Comm'

    def __init__(self, file: StringIO):
        Converter.__init__(self, file)
        self.data: List[Dict[str, str]] = []
        self.__parse_csv()

    def convert(self) -> List[TaxRecord]:
        if len(self.data) == 0:
            return []

        tax_report = []
        for record in self.data:
            action = self.__get_action(record)
            if action:
                date = self.__get_date(record)
                index = self.__get_index(record)
                asset = self.__get_asset(record)
                quantity = self.__get_quantity(record, action)
                price = CurrencyConverter(self.__get_price(record)).convert_to_gbp(date).amount
                split = StockSplit(index, quantity, price, date)
                tax_report.append(TaxRecord(date, asset, split.quantity(), split.price(), Decimal(0)))

        logging.warning(tax_report)

        return tax_report

    def __get_action(self, data: Dict[str, str]) -> Optional[EquityAction]:
        try:
            action_str: str = data[SchwabTransactionsConverter.ACTION_COLUMN_KEY].upper()
            return EquityAction[action_str]
        except KeyError as _:
            logging.debug('Cannot parse equity action from: {}'.format(data))
            return None

    def __get_date(self, data: Dict[str, str]) -> datetime:
        degiro_date_str: str = data[SchwabTransactionsConverter.DATE_COLUMN_KEY]
        return datetime.strptime(degiro_date_str, SchwabTransactionsConverter.SCHWAB_DATE_FORMAT)

    def __get_index(self, data: Dict[str, str]) -> str:
        return data[SchwabTransactionsConverter.PRODUCT_COLUMN_KEY]

    def __get_asset(self, data: Dict[str, str]) -> str:
        index = IndexRenaming(
            data[SchwabTransactionsConverter.PRODUCT_COLUMN_KEY],
            data[SchwabTransactionsConverter.DESCRIPTION_COLUMN_KEY],
        )
        return index.actual_definition()

    def __get_quantity(self, data: Dict[str, str], action: EquityAction) -> Decimal:
        if action == EquityAction.BUY:
            return Decimal(data[SchwabTransactionsConverter.QUANTITY_COLUMN_KEY])
        elif action == EquityAction.SELL:
            return -Decimal(data[SchwabTransactionsConverter.QUANTITY_COLUMN_KEY])
        else:
            return Decimal(0)

    def __get_price(self, data: Dict[str, str]) -> Money:
        value = data[SchwabTransactionsConverter.PRICE_COLUMN_KEY]
        value = value.replace('$', '')
        return Money(abs(Decimal(value)), 'USD')

    def __get_fee(self, data: Dict[str, str]) -> Money:
        value = data[SchwabTransactionsConverter.FEES_COLUMN_KEY]
        value = value.replace('$', '')
        return Money(abs(Decimal(value)), 'USD')

    def __parse_csv(self):
        if len(self.rawdata) <= 2:
            return

        self.header = self.rawdata[1]
        self.header_length = len(self.header)

        for row_number in range(2, len(self.rawdata)):
            object: Dict[str, str] = {}
            counter = 0
            for key in self.header:
                object[key] = self.rawdata[row_number][counter]
                counter += 1
            self.data.append(object)

        logging.warning(self.data)



