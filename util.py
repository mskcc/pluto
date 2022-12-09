import os
import csv
import json
import gzip
import hashlib
from collections import OrderedDict
from typing import List, Dict, Tuple, Union

def write_table(
    tmpdir: str, # path to parent directory to save the file to
    filename: str, # basename for the file to write to
    lines: List[ List[str] ], # a list of lists, containing each field to write
    delimiter: str = '\t', # character to join the line elements on
    filepath: str = None # full path to write the output file to; overrides tmpdir and filename
    ) -> str:
    """
    Write a table to a temp location
    """
    if not filepath:
        filepath = os.path.join(tmpdir, filename)
    with open(filepath, "w") as f:
        for line in lines:
            line_str = delimiter.join(line) + '\n'
            f.write(line_str)
    return(filepath)


def dicts2lines(
    dict_list: List[Dict], # a list of dictionaries with data to be written
    comment_list: List[ List[str] ] = None # a list of comment lines to prepend to the file data
    ) -> List[ List[str] ]:
    """
    Helper function to convert a list of dicts into a list of lines to use with write_table
    create a list of line parts to pass for write_table

    Note
    -----
    Returns list of lines in the format::

        [ ['# comment1'], ['col1', 'col2'], ['val1', 'val2'], ... ]

    Note
    ----
    Dict values must be type `str`

    Examples
    --------
    Example usage::

        >>> comments = [ ['# foo'] ]
        >>> row1 = { 'a':'1', 'b':'2' }
        >>> row2 = { 'a':'6', 'b':'7' }
        >>> lines = dicts2lines(dict_list = [row1, row2], comment_list = comments)
        >>> lines
        [ ['# foo'], ['a', 'b'], ['1', '2'], ['6', '7']]
        >>> output_path = write_table(tmpdir = '.', filename = 'output.txt', lines = lines)

    """
    fieldnames = OrderedDict() # use as an ordered set
    # get the ordered fieldnames
    for row in dict_list:
        for key in row.keys():
            fieldnames[key] = ''
    # list to hold the lines to be written out
    demo_maf_lines = []
    if comment_list:
        for line in comment_list:
            demo_maf_lines.append(line)
    fieldnames = [ f for f in fieldnames.keys() ]
    demo_maf_lines.append(fieldnames)
    for row in dict_list:
        demo_maf_lines.append([ v for v in row.values() ])
    return(demo_maf_lines)

def clean_dicts(
    obj: Union[Dict, List],
    bad_keys: List[str] = ('nameext', 'nameroot'),
    related_keys: List[ Tuple[str, str, List[str]] ] = None):
    """
    Recursively remove all bad_keys from all dicts in the input obj
    Also, use "related_keys" to conditionally remove certain keys if a specific key:value pair is present
    If `obj` is a list, all items are recursively searched for dicts containuing keys for scrubbing
    If `obj` is a dict, keys are scrubbed
    If any `obj` values are lists or dicts, they are recursively scrubbed as well

    NOTE: this depends on `obj` being mutable and maintaining state between recursion calls...

    TODO: implement a version that can match `related_keys` on file extension like .html, .gz, etc..

        # remove some dict keys
        d = {'a':1, 'nameext': "foo"}
        expected = {'a':1}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        # remove some dict keys if a given key matches a given value
        # related_keys = [("key_foo", "value_foo", ["badkey1", "badkey2"]),
        #                 ("key_bar", "value_bar", ["badkey1", "badkey2"]), ... ]
        d = {'basename': "report.html", "class": "File", 'size': "1", "checksum": "foobar"}
        related_keys = [('basename', "report.html", ['size', 'checksum'])]
        expected = {'basename': "report.html", "class": "File"}
        clean_dicts(d, related_keys = related_keys)
        self.assertDictEqual(d, expected)

    """
    if related_keys is None:
        related_keys = []

    # remove bad keys from top-level dict keys
    if isinstance(obj, dict):
        # ~~~~~~~~~ #
        # NOTE: This is the terminal case for the recursion loop !!
        # remove each key in the dict that is recognized as being unwanted
        for bad_key in bad_keys:
            obj.pop(bad_key, None)

        # remove each unwanted key in the dict if some other key:value pair is found
        for key_map in related_keys:
            key = key_map[0] # key_map = ("key_foo", "value_foo", ["key1", "key2"])
            value = key_map[1]
            remove_keys = key_map[2] # probably need some kind of type-enforcement here
            if (key, value) in obj.items():
                for remove_key in remove_keys:
                    obj.pop(remove_key, None)
        # ~~~~~~~~~ #

        # recurse to clear out bad keys from nested list values
        # obj = { 'foo': [i, j, k, ...],
        #         'bar': {'baz': [q, r, s, ...]} }
        for key in obj.keys():
            # 'foo': [i, j, k, ...]
            if isinstance(obj[key], list):
                for i in obj[key]:
                    clean_dicts(obj = i, bad_keys = bad_keys, related_keys = related_keys)

            # 'bar': {'baz': [q, r, s, ...]}
            elif isinstance(obj[key], dict):
                clean_dicts(obj = obj[key], bad_keys = bad_keys, related_keys = related_keys)

    # recurse to clear out bad keys from nested list values
    elif isinstance(obj, list):
        for item in obj:
            clean_dicts(obj = item, bad_keys = bad_keys, related_keys = related_keys)

def parse_header_comments(
    filename: str, # path to input file
    comment_char: str = '#', # comment character
    ignore_comments: bool = False) -> Tuple[ List[str], int ]:
    """
    Parse a file with comments in its header to return the comments and the line number to start reader from.

    Examples
    --------
    Example usage::

        comments, start_line = parse_header_comments(filename)
        with open(portal_file) as fin:
            while start_line > 0:
                next(fin)
                start_line -= 1
            reader = csv.DictReader(fin, delimiter = '\t') # header_line = next(fin)
            portal_lines = [ row for row in reader ]
    """
    comments = []
    start_line = 0

    is_gz = False
    if filename.endswith('.gz'):
        is_gz = True

    if is_gz:
        fin = gzip.open(filename, 'rt')
    else:
        fin = open(filename)

    # find the first line without comments
    for i, line in enumerate(fin):
        if str(line).startswith(comment_char):
            if not ignore_comments:
                comments.append(line.strip())
            start_line += 1
        else:
            break
    fin.close()
    return(comments, start_line)

def load_mutations(
        filename: str, # input file name
        strip: bool = False, # strip some extra keys from the mutations
        strip_keys: list = ('all_effects', 'Consequence', 'Variant_Classification')
        ) -> Tuple[ List[str], List[Dict] ]:
    """
    Load the mutations from a tabular .maf file

    Examples
    --------
    Example usage::

        >>> row1 = {'Hugo_Symbol': 'SOX9', 'Chromosome': '1'}
        >>> row2 = {'Hugo_Symbol': 'BRCA', 'Chromosome': '7'}
        >>> comments = [ ['# version 2.4'] ]
        >>> lines = dicts2lines([row1, row2], comments)
        >>> output_path = write_table('.', 'output.maf', lines)
        >>> comments, mutations = load_mutations(output_path)
        >>> comments
        ['# version 2.4']
        >>> mutations
        [OrderedDict([('Hugo_Symbol', 'SOX9'), ('Chromosome', '1')]), OrderedDict([('Hugo_Symbol', 'BRCA'), ('Chromosome', '7')])]

    Notes
    -----
    Loads all mutation records into memory at once; for large datasets use TableReader to iterate over records instead
    """
    comments, start_line = parse_header_comments(filename)

    is_gz = False
    if filename.endswith('.gz'):
        is_gz = True

    if is_gz:
        fin = gzip.open(filename, 'rt')
    else:
        fin = open(filename)

    # with open(filename) as fin:
    while start_line > 0:
        next(fin)
        start_line -= 1
    reader = csv.DictReader(fin, delimiter = '\t')
    mutations = [ row for row in reader ]

    if strip:
        for mut in mutations:
            for key in strip_keys:
                mut.pop(key, None)

    fin.close()
    return(comments, mutations)

def md5_file(filename: str) -> str:
    """
    Get md5sum of a file by reading it in small chunks. This avoids issues with Python memory usage when hashing large files.
    """
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
    hash = file_hash.hexdigest()
    return(hash)


def md5_obj(obj: object) -> str:
    """
    Get the md5sum of a Python object in memory by converting it to JSON
    """
    hash = hashlib.md5(json.dumps(obj, sort_keys=True).encode('utf-8')).hexdigest()
    return(hash)