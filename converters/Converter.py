import csv
from io import StringIO
from typing import List, Dict


class Converter:
    def __init__(self, file: StringIO):
        self.file = file

        self.rawdata: List[str] = []
        self.data: List[Dict[str, str]] = []
        self.__parse()

    def convert(self):
        raise NotImplementedError("Please implement convert in the child class")


    def __parse(self):
        reader = csv.reader(self.file, delimiter=',', quotechar='"')
        for row in reader:
            self.rawdata.append(row)

        if len(self.rawdata) >= 1:
            self.header = self.rawdata[0]

        if len(self.rawdata) == 1:
            return

        for row_number in range(1, len(self.rawdata)):
            object: Dict[str, str] = {}
            counter = 0
            previous_key = None
            for key in self.header:
                if not key:
                    if not previous_key:
                        raise Exception('Previous key cannot be None, parser failed')

                    key = previous_key + ' currency'
                object[key] = self.rawdata[row_number][counter]
                previous_key = key
                counter += 1
            self.data.append(object)



