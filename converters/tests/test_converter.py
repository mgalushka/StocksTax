import os
import unittest
from pathlib import Path

from File import File
from converters.Converter import Converter
from tests.test_data import TestData


class TestConverter(unittest.TestCase):

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            Converter(File('/dummy').get_io())

    def test_file_found(self):
        filepath = self.__given_empty_file('/tmp/dummy.csv')
        converter = Converter(File(filepath).get_io())
        with self.assertRaises(NotImplementedError):
            converter.convert()

        self.__cleanup(filepath)

    def test_correct_file(self):
        filepath = self.__given_correct_file('/tmp/dummy.csv')
        converter = Converter(File(filepath).get_io())
        data = converter.rawdata
        self.assertEqual(4, len(data))

        self.__cleanup(filepath)

    def __given_empty_file(self, path):
        file = Path(path)
        if file.exists():
            return path

        fp = open(path, 'x')
        fp.close()
        return path

    def __given_correct_file(self, path):
        file = Path(path)
        if file.exists():
            return path

        fp = open(path, 'w')
        fp.write(TestData.CORRECT_DEGIRO_MULTILINE_SAMPLE)
        fp.close()
        return path

    def __cleanup(self, path):
        os.remove(path)
