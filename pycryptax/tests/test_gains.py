import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from pycryptax.csvdata import CSVTransactionGains, TransactionGainTx
from pycryptax.gains import CapitalGainCalculator

class TestGains(unittest.TestCase):

    def setThisUp(self):
        config = {'isdir.return_value': False}
        self.patcher1 = patch('os.path', **config)
        self.patcher1.start()

        config2 = {'_processFile.return_value': None}
        self.patcher2 = patch('pycryptax.csvdata.CSVDateMap', **config2)
        self.patcher2.start()

    def tearThisDown(self):
        self.patcher1.stop()
        self.patcher2.stop()

    @patch('pycryptax.csvdata.CSVDateMap._processFile')
    @patch('os.path.isdir')
    def _test_double_match(self, _, __):
        self.setThisUp()
        gainData = CSVTransactionGains("", requireDir=False)
        gainData.insert(
            datetime(2020, 1, 1),
            TransactionGainTx(
                'MSFT', 50, Decimal(1.0), Decimal(0.5)
            )
        )
        gainData.insert(
            datetime(2020, 1, 2),
            TransactionGainTx(
                'MSFT', -20, Decimal(2.0), Decimal(0.6)
            )
        )
        gainData.insert(
            datetime(2020, 1, 3),
            TransactionGainTx(
                'MSFT', 10, Decimal(3.0), Decimal(0.7)
            )
        )

        c = CapitalGainCalculator(gainData, None, datetime(2019, 4, 6), datetime(2020, 4, 5))
        c.printSummary()
        self.tearThisDown()
