import os
import unittest
from pathlib import Path

from converters.Converter import Converter


class TestConverter(unittest.TestCase):

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            Converter('/dummy')

    def test_file_found(self):
        filepath = self.__given_file('/tmp/dummy.csv')
        converter = Converter(filepath)
        with self.assertRaises(NotImplementedError):
            converter.convert()

        self.__cleanup(filepath)

    def __given_file(self, path):
        file = Path(path)
        if file.exists():
            return path

        fp = open(path, 'x')
        fp.close()
        return path

    def __cleanup(self, path):
        os.remove(path)
