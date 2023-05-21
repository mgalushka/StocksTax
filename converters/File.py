from io import StringIO
from pathlib import Path

class File:
    def __init__(self, filepath: str):
        self.filepath = filepath
        if not self.__validate_filepath():
            raise FileNotFoundError(self.filepath)

    def get_io(self) -> StringIO:
        with open(self.filepath) as file:
            data = file.read()
        return StringIO(data)

    def __validate_filepath(self) -> bool:
        path: Path = Path(self.filepath)
        return path.is_file() and path.exists()