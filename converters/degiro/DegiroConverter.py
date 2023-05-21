from datetime import datetime
from decimal import Decimal
from typing import List, Dict

from TaxRecord import TaxRecord
from converters.Converter import Converter

class DegiroConverter(Converter):

    DEGIRO_DATE_FORMAT = '%d-%m-%Y'

    DATE_COLUMN_KEY = 'Date'
    PRODUCT_COLUMN_KEY = 'Product'
    ISIN_COLUMN_KEY = 'ISIN'

    def convert(self) -> List[TaxRecord]:
        if len(self.data) == 0:
            return []

        tax_report = []
        for record in self.data:
            date = self.__get_date(record)
            tax_report.append(TaxRecord(date, '', Decimal(0), Decimal(0), Decimal(0)))
        return tax_report

    def __get_date(self, data: Dict[str, str]) -> datetime:
        degiro_date_str: str = data[DegiroConverter.DATE_COLUMN_KEY]
        return datetime.strptime(degiro_date_str, DegiroConverter.DEGIRO_DATE_FORMAT)

    def __get_asset(self, data: Dict[str, str]) -> str:
        return '{product} (ISIN: {isin})'.format(
            product=data[DegiroConverter.PRODUCT_COLUMN_KEY],
            isin=data[DegiroConverter.ISIN_COLUMN_KEY]
        )