import unittest
from datetime import datetime
from decimal import Decimal

from TaxRecord import TaxRecord


class TestTaxRecord(unittest.TestCase):

    def test_tax_record_string(self):
        record_date: str = '2022-01-22'
        asset: str = 'Something'
        record = TaxRecord(datetime.strptime(record_date, '%Y-%m-%d'), asset, Decimal(0), Decimal(0), Decimal(0))
        self.assertEqual('{},{},0,0,0'.format(record_date, asset), str(record))