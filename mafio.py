import csv
from typing import TextIO, List, Dict, Generator
try:
    from .util import (
        dicts2lines,
        parse_header_comments,
    )
except ImportError:
    from util import (
        dicts2lines,
        parse_header_comments,
    )


class TableReader(object):
    """
    Handler for reading a table with comments

    Allows for parsing file attributes and rows without loading the whole file into memory

    Note
    ----
    Input file must have column headers!


    ----
    NOTE: See

    helix_filters_01.bin.cBioPortal_utils.TableReader
    helix_filters_01.bin.cBioPortal_utils.MafReader
    helix_filters_01.bin.cBioPortal_utils.MafWriter

    https://github.com/mskcc/helix_filters_01/blob/master/bin/cBioPortal_utils.py
    """
    def __init__(self,
        filename: str,
        comment_char: str = '#',
        delimiter: str = '\t',
        ignore_comments: bool = False):
        """
        Parameters
        ----------
        filename: str
            path to input file
        comment_char: str
            comment character for the file
        delimiter: str
            file field delimiter

        Examples
        --------
        Example usage::

            table_reader = TableReader(input_maf_file)
            comment_lines = table_reader.comment_lines
            fieldnames = table_reader.get_fieldnames()
            records = [ rec for rec in table_reader.read() ]
        """
        self.filename = filename
        self.comment_char = comment_char
        self.delimiter = delimiter
        # get the comments from the file and find the beginning of the table header
        self.comments = None
        self.comment_lines = []
        self.comments, self.start_line = parse_header_comments(filename, comment_char = self.comment_char, ignore_comments = ignore_comments)
        if self.comments:
            self.comment_lines = [ c + '\n' for c in self.comments ]

    def get_reader(self, fin: TextIO) -> csv.DictReader:
        """
        returns the csv.DictReader for the table rows, skipping the comments
        """
        start_line = self.start_line
        # skip comment lines
        while start_line > 0:
            next(fin)
            start_line -= 1
        reader = csv.DictReader(fin, delimiter = self.delimiter)
        return(reader)

    def get_fieldnames(self) -> List[str]:
        """
        returns the list of fieldnames for the table
        """
        with open(self.filename,'r') as fin:
            reader = self.get_reader(fin)
            return(reader.fieldnames)

    def read(self) -> Generator[Dict, None, None]:
        """
        iterable to get the record rows from the table, skipping the comments
        """
        with open(self.filename,'r') as fin:
            reader = self.get_reader(fin)
            for row in reader:
                yield(row)

    def count(self) -> int:
        """
        Return the total number of records in the table
        """
        num_records = 0
        for _ in self.read():
            num_records += 1
        return(num_records)


class MafWriter(csv.DictWriter):
    """
    Wrapper around csv.DictWriter for handling maf lines that provides required default values;
    csv.DictWriter(f, fieldnames = fieldnames, delimiter = '\t', lineterminator='\n')

    NOTE: see this solution if we want to output the raw file lines instead https://stackoverflow.com/questions/29971718/reading-both-raw-lines-and-dicionaries-from-csv-in-python
    Since we have to make assumptions about the delimiter and lineterminator its easier to just use csv.DictWriter directly anyway

    https://github.com/python/cpython/blob/12803c59d54ff1a45a5b08cef82652ef199b3b07/Lib/csv.py#L130

    ----
    NOTE: See

    helix_filters_01.bin.cBioPortal_utils.TableReader
    helix_filters_01.bin.cBioPortal_utils.MafReader
    helix_filters_01.bin.cBioPortal_utils.MafWriter

    https://github.com/mskcc/helix_filters_01/blob/master/bin/cBioPortal_utils.py
    """
    def __init__(
        self,
        f: TextIO,
        fieldnames: List[str],
        delimiter: str = '\t',
        lineterminator: str ='\n',
        comments: List[str] = None,
        write_comments: bool = True,
        *args, **kwargs):
        super().__init__(f, fieldnames = fieldnames, delimiter = delimiter, lineterminator=lineterminator, *args, **kwargs)
        if comments:
            if write_comments:
                for line in comments:
                    f.write(line) # + lineterminator ; comments should have newline appended already
