import unittest
from datetime import datetime
from io import StringIO

from degiro.DegiroConverter import DegiroConverter
from tests.test_data import TestData


class TestDegiroParser(unittest.TestCase):

    def test_degiro_date(self):
        converter = DegiroConverter(self.__given_correct_degiro_data())
        data = converter.data
        self.assertEqual('21-09-2022', data[0][DegiroConverter.DATE_COLUMN_KEY])

    def test_degiro_date_convert(self):
        converter = DegiroConverter(self.__given_correct_degiro_data())
        tax_records = converter.convert()
        self.assertEqual(1, len(tax_records))
        self.assertEqual(datetime.strptime('21-09-2022', DegiroConverter.DEGIRO_DATE_FORMAT), tax_records[0].date)

    def __given_correct_degiro_data(self) -> StringIO:
        return StringIO(TestData.CORRECT_DEGIRO_SMALL_SAMPLE)