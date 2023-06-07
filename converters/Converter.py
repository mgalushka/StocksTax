import csv
from io import StringIO
from typing import List


class Converter:
    def __init__(self, file: StringIO, log: StringIO):
        self.file = file
        self.log = log
        self.rawdata: List[str] = []
        self.__parse()

    def convert(self):
        raise NotImplementedError("Please implement convert in the child class")

    def __parse(self):
        reader = csv.reader(self.file, delimiter=',', quotechar='"')
        for row in reader:
            self.rawdata.append(row)






