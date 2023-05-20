from pathlib import Path

class Converter:
    def __init__(self, filepath: str):
        self.filepath = filepath
        if not self.__validate_filepath():
            raise FileNotFoundError(self.filepath)

    def convert(self):
        raise NotImplementedError("Please implement convert in the child class")

    def __validate_filepath(self):
        path = Path(self.filepath)
        return path.is_file() and path.exists()