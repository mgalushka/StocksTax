import logging
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import List, Dict

from Converter import Converter
from IndexRenaming import IndexRenaming
from Money import Money
from TaxRecord import TaxRecord
from currency.CurrencyConverter import CurrencyConverter


class SchwabEquityAwardConverter(Converter):

    SCHWAB_DATE_FORMAT = '%m/%d/%Y'

    DATE_COLUMN_KEY = 'Date'
    PRODUCT_COLUMN_KEY = 'Symbol'
    QUANTITY_COLUMN_KEY = 'Net Shares Deposited'
    PRICE_COLUMN_KEY = 'Fair Market Value'

    def __init__(self, file: StringIO):
        Converter.__init__(self, file)
        self.data: List[Dict[str, str]] = []
        self.__parse_csv()

    def convert(self) -> List[TaxRecord]:
        if len(self.data) == 0:
            return []

        tax_report = []
        for record in self.data:
            date = self.__get_date(record)
            asset = self.__get_asset(record)
            quantity = self.__get_quantity(record)
            price = CurrencyConverter(self.__get_price(record)).convert_to_gbp(date).amount
            tax_report.append(TaxRecord(date, asset, quantity, price, Decimal(0)))

        return tax_report

    def __get_date(self, data: Dict[str, str]) -> datetime:
        degiro_date_str: str = data[SchwabEquityAwardConverter.DATE_COLUMN_KEY]
        return datetime.strptime(degiro_date_str, SchwabEquityAwardConverter.SCHWAB_DATE_FORMAT)

    def __get_asset(self, data: Dict[str, str]) -> str:
        index = IndexRenaming(
            data[SchwabEquityAwardConverter.PRODUCT_COLUMN_KEY],
            '',
        )
        return index.actual_definition()

    def __get_quantity(self, data: Dict[str, str]) -> Decimal:
        return Decimal(data[SchwabEquityAwardConverter.QUANTITY_COLUMN_KEY])

    def __get_price(self, data: Dict[str, str]) -> Money:
        value = data[SchwabEquityAwardConverter.PRICE_COLUMN_KEY]
        value = value.replace('$', '')
        return Money(abs(Decimal(value)), 'USD')

    def __parse_csv(self):
        if len(self.rawdata) >= 1:
            self.main_header = self.rawdata[1]
            self.main_header_length = len(self.main_header)

        if len(self.rawdata) == 1:
            return

        subheader = None
        current_item = {}
        for row_number in range(2, len(self.rawdata)):
            # main values
            if (row_number - 2) % 3 == 0:
                current_item = {}
                for value_index in range(0, self.main_header_length):
                    key_name = self.main_header[value_index]
                    if key_name:
                        current_item[self.main_header[value_index]] = self.rawdata[row_number][value_index]

            if (row_number - 2) % 3 == 1:
                subheader = self.rawdata[row_number]

            if (row_number - 2) % 3 == 2:
                for value_index in range(0, len(subheader)):
                    key_name = subheader[value_index]
                    if key_name:
                        current_item[key_name] = self.rawdata[row_number][value_index]
                self.data.append(current_item)

        logging.warning(self.data)


