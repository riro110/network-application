from typing import Iterator, List, Tuple
from dataclasses import dataclass


@dataclass
class File:
    filename: str


class FileSet:
    def __init__(self):
        self.file_list: List[File] = []

    def add_file(self, file: File) -> None:
        self.file_list.append(file)

    def search_file(self, filename: str) -> Iterator[Tuple[int, File]]:
        for idx, file in enumerate(self.file_list):
            if filename in file.filename:
                yield idx, file
