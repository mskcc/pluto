"""
Helper functions for running tests
"""
import sys
import os
import subprocess as sp
import csv
import json
try:
    from .settings import CWL_ARGS, TOIL_ARGS, DATA_SETS, KNOWN_FUSIONS_FILE, IMPACT_FILE, USE_LSF, TMP_DIR, PRESERVE_TEST_DIR, CWL_ENGINE, PRINT_COMMAND
    from .settings import CWL_DIR as _CWL_DIR
except ImportError:
    from settings import CWL_ARGS, TOIL_ARGS, DATA_SETS, KNOWN_FUSIONS_FILE, IMPACT_FILE, USE_LSF, TMP_DIR, PRESERVE_TEST_DIR, CWL_ENGINE, PRINT_COMMAND
    from settings import CWL_DIR as _CWL_DIR
from collections import OrderedDict
import unittest
from tempfile import mkdtemp
import shutil
from pathlib import Path
import getpass
import hashlib
from copy import deepcopy
from typing import Union, List, Tuple, Dict, TextIO, Generator

username = getpass.getuser()


class CWLFile(os.PathLike):
    """
    Wrapper class to locate the full path to a cwl file more conveniently
    """
    def __init__(self, path: str, CWL_DIR: str = None):
        """
        Parameters
        ----------
        path: str
            name of a CWL file relative to `CWL_DIR`
        CWL_DIR: str
            full path to the directory containing CWL files


        Examples
        --------
        Example usage::

            cwl_file = CWLFile("foo.cwl")
        """
        if CWL_DIR is None:
            CWL_DIR = _CWL_DIR
        self.path = os.path.join(CWL_DIR, path)
    def __str__(self):
        return(self.path)
    def __repr__(self):
        return(self.path)
    def __fspath__(self):
        return(self.path)

class InvalidEngine(Exception):
    pass

class CWLRunner(object):
    """
    class for running a CWL File
    """
    def __init__(self,
        cwl_file: Union[str, CWLFile], # str or CWLFile
        input: dict, # pipeline input dict to be converted to JSON
        # CWL_ARGS = CWL_ARGS,
        print_stdout: bool = False,
        dir: str = None, # directory to run the CWL in and write output to
        output_dir: str = None, # directory to save output files to
        input_json_file: str = None, # path to write input JSON to if you already have one chosen
        input_is_file: bool = False, # if the `input` arg should be treated as a pre-made JSON file and not a Python dict
        verbose: bool = True,
        testcase: unittest.TestCase = None,
        engine: str = "cwltool", # default engine is cwl-runner cwltool
        print_command: bool = False,
        restart: bool = False,
        jobStore: str = None,
        debug: bool = False,
        leave_tmpdir: bool = False,
        leave_outputs: bool = False,
        parallel: bool = False,
        js_console: bool = False,
        print_stderr: bool = False,
        use_cache: bool = True
        ):
        """
        Parameters
        ----------
        cwl_file: str | CWLFile
            CWL file path or CWLFile object to run
        input: dict
            data dict to be used as input to the CWL
        CWL_ARGS: list
            list of extra command line arguments to include when running the CWL workflow
        print_stdout: bool
            whether stdout from the CWL workflow should be printed to console
        dir: str
            directory to run the CWL workflow in; if `None`, a temp dir will be created automatically
        output_dir: str
            output directory for the CWL workflow; if `None`, defaults to 'output' inside the `dir` directory
        input_json_file: str
            path to the input.json file to write CWL input data to
        input_is_file: bool
            if the `input` arg should be treated as a pre-made JSON file path and not a Python dict object
        verbose: bool
            include descriptive messages in console stdout when running CWL
        testcase: unittest.TestCase
            `unittest.TestCase` object to use when making assertions when running as part of a unit test
        engine: str
            run the CWL with cwl-runner (`"cwltool"`) or Toil (`"toil"`)
        print_command: bool
            print the fully evaluated command to console before running
        restart: bool
            enable "restart" or "resume" functionality when running the CWL workflow
        jobStore: str
            Toil job store to use when restarting a pipeline
        debug: bool
            whether to include the `--debug` arg with the CWL runner command for extra console output in case of error and debugging
        leave_tmpdir: bool
            do not delete the tmp dir after the CWL workflow finishes
        leave_outputs: bool
            do not delete the output dir after completion
        parallel: bool
            run workflow jobs in parallel; NOTE: make sure all Singularity containers are cached first or it will break


        Examples
        --------
        Example usage::

            runner = CWLRunner(
                cwl_file = "/path/to/tool.cwl",
                input = cwl_input,
                dir = "/run/workflow/here",
                verbose = True)
            output_json, output_dir, output_json_file = runner.run()
        """
        self.cwl_file = cwl_file
        self.input = input
        # self.CWL_ARGS = CWL_ARGS
        self.print_stdout = print_stdout
        self.verbose = verbose
        self.input_json_file = input_json_file
        self.testcase = testcase
        self.engine = engine
        self.print_command = print_command
        self.restart = restart
        self.jobStore = jobStore
        self.debug = debug
        self.leave_tmpdir = leave_tmpdir
        self.leave_outputs = leave_outputs
        self.parallel = parallel
        self.output_dir = output_dir
        self.input_is_file = input_is_file
        self.js_console = js_console
        self.print_stderr = print_stderr
        self.use_cache = use_cache

        # override some settings from env vars
        if PRINT_COMMAND:
            self.print_command = PRINT_COMMAND

        if dir is None:
            if engine == 'cwltool':
                dir = "cwltool_output"
            elif engine == 'toil':
                dir = "toil_output"
            else:
                dir = "pipeline_output"

        Path(os.path.abspath(dir)).mkdir(parents=True, exist_ok=True)
        self.dir = os.path.abspath(dir)

    def run(self) -> Tuple[int, str, str]:
        """
        Run the CWL workflow object
        """
        if self.verbose:
            message = ">>> Running {cwl_file} in {dir}".format(cwl_file = self.cwl_file, dir = self.dir)
            print(message)

        if self.engine == 'cwltool':
            output_json, output_dir = run_cwl(
                testcase = self.testcase,
                tmpdir = self.dir,
                input_json = self.input,
                cwl_file = self.cwl_file,
                # CWL_ARGS = self.CWL_ARGS,
                print_stdout = self.print_stdout,
                print_command = self.print_command,
                check_returncode = False,
                input_json_file = self.input_json_file,
                debug = self.debug,
                leave_tmpdir = self.leave_tmpdir,
                leave_outputs = self.leave_outputs,
                parallel = self.parallel,
                output_dir = self.output_dir,
                input_is_file = self.input_is_file,
                js_console = self.js_console,
                print_stderr = self.print_stderr,
                use_cache = self.use_cache
                )
        elif self.engine == 'toil':
            output_json, output_dir = run_cwl_toil(
                input_data = self.input,
                cwl_file = self.cwl_file,
                run_dir = self.dir,
                print_command = self.print_command,
                input_json_file = self.input_json_file,
                restart = self.restart,
                jobStore = self.jobStore,
                input_is_file = self.input_is_file,
                testcase = self.testcase
                )
        else:
            # TODO: what should we do in the case where the engine doesnt match one of the above??
            # This should probably raise an error
            raise InvalidEngine(">>> ERROR: invalid engine provided: {}. Try 'cwltool' or 'toil'".format(self.engine))

        output_json_file = os.path.join(self.dir, "output.json")
        with open(output_json_file, "w") as fout:
            json.dump(output_json, fout, indent = 4)
        return(output_json, output_dir, output_json_file)















def run_command(
    args: List[str],
    testcase: unittest.TestCase = None,
    validate: bool = False,
    print_stdout: bool = False) -> Tuple[int, str, str]:
    """
    Helper function to run a shell command easier

    Parameters
    ----------
    args: list
        a list of shell args to execute
    validate: bool
        whether to check that the exit code was 0; requires `testcase`
    testcase: unittest.TestCase
        a test case instance for making assertions

    Returns
    -------
    int
        the command return code
    str
        the command stdout
    str
        the command stderr

    Examples
    -------
    Example usage::

        command = [ "foo.py", "arg1", "arg2" ]
        returncode, proc_stdout, proc_stderr = run_command(command, testcase = self, validate = True)
    """
    process = sp.Popen(args, stdout = sp.PIPE, stderr = sp.PIPE, universal_newlines = True)
    proc_stdout, proc_stderr = process.communicate()
    returncode = process.returncode
    proc_stdout = proc_stdout.strip()
    proc_stderr = proc_stderr.strip()

    if print_stdout:
        print(proc_stdout)

    # check that it ran successfully; requires testcase to be passed !
    if validate:
        if returncode != 0:
            print(proc_stderr)
        testcase.assertEqual(returncode, 0)
    return(returncode, proc_stdout, proc_stderr)

def run_cwl(
    tmpdir: str, # dir where execution is taking place and files are staged & written
    input_json: dict, # CWL input data
    cwl_file: Union[str, CWLFile], # CWL file to run
    # CWL_ARGS = CWL_ARGS, # default cwltool args to use
    testcase: unittest.TestCase = None, # 'self' in the unittest.TestCase instance
    CLI_ARGS: List[str] = None,
    print_stdout: bool = False,
    print_command: bool = False,
    check_returncode: bool = True,
    input_json_file: str = None,
    debug: bool = False,
    leave_tmpdir: bool = False,
    leave_outputs: bool = False,
    parallel: bool = False,
    output_dir: str = None,
    input_is_file: bool = False, # if the `input_json` is actually a path to a pre-existing JSON file
    js_console: bool = False,
    print_stderr: bool = False,
    use_cache: bool = True
    ) -> Tuple[Dict, str]:
    """
    Run the CWL with cwltool / cwl-runner

    Returns
    -------
    dict:
        output data dictionary loaded from CWL stdout JSON
    str:
        path to the `output` directory from the CWL workflow
    """
    if CLI_ARGS is None:
        CLI_ARGS = CWL_ARGS

    if not input_is_file:
        # the input_json is a Python dict that needs to be dumped to file
        if not input_json_file:
            input_json_file = os.path.join(tmpdir, "input.json")
        with open(input_json_file, "w") as json_out:
            json.dump(input_json, json_out)
    else:
        # input_json is a pre-existing JSON file
        input_json_file = input_json

    if output_dir is None:
        output_dir = os.path.join(tmpdir, "output")
    cache_dir = os.path.join(tmpdir, 'tmp', "cache")
    tmp_dir = os.path.join(tmpdir, 'tmp', "tmp")

    if leave_outputs:
        CLI_ARGS = [ *CLI_ARGS, '--leave-outputs' ]
    if leave_tmpdir:
        CLI_ARGS = [ *CLI_ARGS, '--leave-tmpdir' ]
    if debug:
        CLI_ARGS = [ *CLI_ARGS, '--debug' ]
    if parallel:
        print(">>> Running cwl-runner with 'parallel'; make sure all Singularity containers are pre-cached!")
        # if the containers are not already all pre-pulled then it can cause issues with parallel jobs all trying to pull the same container to the same filepath
        CLI_ARGS = [ *CLI_ARGS, '--parallel' ]
    if js_console:
        CLI_ARGS = [ *CLI_ARGS, '--js-console' ]

    if use_cache:
        CLI_ARGS = [ *CLI_ARGS, '--cachedir', cache_dir ]

    command = [
        "cwl-runner",
        *CLI_ARGS,
        "--outdir", output_dir,
        "--tmpdir-prefix", tmp_dir,
        # "--cachedir", cache_dir,
        cwl_file, input_json_file
        ]
    if print_command:
        print(">>> cwl-runner command:")
        print(' '.join([ str(c) for c in  command ]) )

    returncode, proc_stdout, proc_stderr = run_command(command)


    if print_stdout:
        print(proc_stdout)

    if print_stderr:
        print(proc_stderr)

    if returncode != 0:
        print(proc_stderr)

    if check_returncode:
        testcase.assertEqual(returncode, 0)

    output_json = json.loads(proc_stdout)
    return(output_json, output_dir)

def run_cwl_toil(
        input_data: Dict,
        cwl_file: Union[str, CWLFile],
        run_dir: str,
        testcase: unittest.TestCase = None, # 'self' in the unittest.TestCase instance
        output_dir: str = None,
        workDir: str = None,
        jobStore: str = None,
        tmpDir: str = None,
        logFile: str = None,
        input_json_file: str = None,
        print_command: bool = False,
        restart: bool = False,
        CLI_ARGS: List[str] = None,
        input_is_file: bool = False, # if the `input_json` is actually a path to a pre-existing JSON file
        print_stdout: bool = False,
        print_stderr: bool = False,
        check_returncode: bool = True # requires testcase instance to be passed as well
        ) -> Tuple[Dict, str]:
    """
    Run a CWL using Toil
    """
    run_dir = os.path.abspath(run_dir)

    if CLI_ARGS is None:
        CLI_ARGS = TOIL_ARGS

    # if we are not restarting, jobStore should not already exist
    if not restart:
        if not jobStore:
            jobStore = os.path.join(run_dir, "jobstore")
        if os.path.exists(jobStore):
            print(">>> ERROR: Job store already exists; ", jobStore)
            sys.exit(1)
        CLI_ARGS = [ *CLI_ARGS, '--jobStore', jobStore ]

    # if we are restarting, jobStore needs to exist
    else:
        if not jobStore:
            print(">>> ERROR: jobStore must be provided")
            sys.exit(1)
        else:
            jobStore = os.path.abspath(jobStore)
        if not os.path.exists(jobStore):
            print(">>> ERROR: jobStore does not exist; ", jobStore)
            sys.exit(1)
        # need to add extra restart args
        CLI_ARGS = [ *CLI_ARGS, '--restart', '--jobStore', jobStore ]

    if not input_is_file:
        # the input_data is a Python dict to be dumped to JSON file
        # if there is already a desired path to dump input data to
        if input_json_file is None:
            input_json_file = os.path.join(run_dir, "input.json")
        # dump input data to JSON file
        with open(input_json_file, "w") as json_out:
            json.dump(input_data, json_out)
    else:
        # input_json is a pre-existing JSON file
        input_json_file = input_data

    if output_dir is None:
        output_dir = os.path.join(run_dir, "output")
    if workDir is None:
        workDir = os.path.join(run_dir, "work")
    if logFile is None:
        logFile = os.path.join(run_dir, "toil.log")
    if tmpDir is None:
        # tmpDir = os.path.join(run_dir, "tmp")
        tmpDir = os.path.join('/scratch', username)

    tmpDirPrefix = os.path.join(tmpDir, "tmp")

    Path(workDir).mkdir(parents=True, exist_ok=True)
    Path(tmpDir).mkdir(parents=True, exist_ok=True)

    command = [
        "toil-cwl-runner",
        *CLI_ARGS,
        "--logFile", logFile,
        "--outdir", output_dir,
        '--workDir', workDir,
        '--tmpdir-prefix', tmpDirPrefix,
        cwl_file, input_json_file
        ]


    if print_command:
        print(">>> toil-cwl-runner command:")
        print(' '.join([ str(c) for c in  command ]) )

    returncode, proc_stdout, proc_stderr = run_command(args = command)

    if print_stdout:
        print(proc_stdout)

    if print_stderr:
        print(proc_stderr)

    if returncode != 0:
        print(proc_stderr)

    if check_returncode:
        testcase.assertEqual(returncode, 0)

    try:
        output_data = json.loads(proc_stdout)
        return(output_data, output_dir)

    # if you cant decode the JSON stdout then it did not finish correctly
    except json.decoder.JSONDecodeError:
        print(proc_stdout)
        print(proc_stderr)
        raise


def parse_header_comments(
    filename: str,
    comment_char: str = '#',
    ignore_comments: bool = False) -> Tuple[ List[str], int ]:
    """
    Parse a file with comments in its header to return the comments and the line number to start reader from.

    Parameters
    ----------
    filename: str
        path to input file
    comment_char: str
        comment character

    Returns
    -------
    list
        a list of comment lines from the file header
    int
        the line number on which file data starts (the line after the last comment)


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
    # find the first line without comments
    with open(filename) as fin:
        for i, line in enumerate(fin):
            if line.startswith(comment_char):
                if not ignore_comments:
                    comments.append(line.strip())
                start_line += 1
            else:
                break
    return(comments, start_line)

def load_mutations(filename: str) -> Tuple[ List[str], List[Dict] ]:
    """
    Load the mutations from a tabular .maf file

    Parameters
    ----------
    filename: str
        path to input file

    Returns
    -------
    list
        a list of comment lines from the file
    list
        a list of dicts containing the records from the file

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
    with open(filename) as fin:
        while start_line > 0:
            next(fin)
            start_line -= 1
        reader = csv.DictReader(fin, delimiter = '\t')
        mutations = [ row for row in reader ]
    return(comments, mutations)

def write_table(
    tmpdir: str,
    filename: str,
    lines: List[ List[str] ],
    delimiter: str = '\t',
    filepath: str = None) -> str:
    """
    Write a table to a temp location

    Parameters
    ----------
    tmpdir: str
        path to parent directory to save the file to
    filename: str
        basename for the file to write to
    filepath: str
        full path to write the output file to; overrides tmpdir and filename
    lines: list
        a list of lists, containing each field to write
    delimiter: str
        character to join the line elements on

    Returns
    -------
    str
        path to output file
    """
    if not filepath:
        filepath = os.path.join(tmpdir, filename)
    with open(filepath, "w") as f:
        for line in lines:
            line_str = delimiter.join(line) + '\n'
            f.write(line_str)
    return(filepath)

def dicts2lines(dict_list: List[Dict], comment_list: List[ List[str] ] = None) -> List[ List[str] ]:
    """
    Helper function to convert a list of dicts into a list of lines to use with write_table
    create a list of line parts to pass for write_table

    Parameters
    ----------
    dict_list: list
        a list of dictionaries with data to be written
    comment_list: list
        a list of comment lines to prepend to the file data

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

def md5_file(filename: str) -> str:
    """
    Get md5sum of a file by reading it in small chunks. This avoids issues with Python memory usage when hashing large files.

    Parameters
    ----------
    filename: str
        path to input file

    Returns
    -------
    str
        hash for the file
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

    Returns
    -------
    str
        the object hash value
    """
    hash = hashlib.md5(json.dumps(obj, sort_keys=True).encode('utf-8')).hexdigest()
    return(hash)


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











class TableReader(object):
    """
    Handler for reading a table with comments

    Allows for parsing file attributes and rows without loading the whole file into memory

    Note
    ----
    Input file must have column headers!
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



class PlutoTestCase(unittest.TestCase):
    """
    An all-in-one `unittest.TestCase` wrapper class that includes a tmpdir, CWLRunner, and other helper functions, to make it easier to create and run unit tests and integration tests for CWL workflows

    Note
    ----
    For usage examples, see https://github.com/mskcc/pluto-cwl/tree/master/tests

    Examples
    --------
    Example usage::

        class TestAddImpactCWL(PlutoTestCase):
            cwl_file = CWLFile('add_af.cwl')

            def test_add_af(self):
                '''Test that the af col gets calculated and added to the maf file correctly'''
                maf_lines = [
                    ['# comment 1'],
                    ['# comment 2'],
                    ['Hugo_Symbol', 't_depth', 't_alt_count'],
                    ['SUFU', '100', '75'],
                    ['GOT1', '100', '1'],
                    ['SOX9', '100', '0'],
                ]

                input_maf = self.write_table(tmpdir = self.tmpdir, filename = 'input.maf', lines = maf_lines)

                self.input = {
                    "input_file": {
                          "class": "File",
                          "path": input_maf
                        },
                    "output_filename":  'output.maf',
                    }
                output_json, output_dir = self.run_cwl()

                expected_output = {
                    'output_file': {
                        'location': 'file://' + os.path.join(output_dir, 'output.maf'),
                        'basename': 'output.maf',
                        'class': 'File',
                        'checksum': 'sha1$39de59ad5d736db692504012ce86d3395685112e',
                        'size': 109,
                        'path': os.path.join(output_dir, 'output.maf')
                        }
                    }
                self.assertDictEqual(output_json, expected_output)

                comments, mutations = self.load_mutations(output_json['output_file']['path'])

                expected_comments = ['# comment 1', '# comment 2']
                self.assertEqual(comments, expected_comments)

                expected_mutations = [
                    {'Hugo_Symbol': 'SUFU', 't_depth': '100', 't_alt_count':'75', 't_af': '0.75'},
                    {'Hugo_Symbol': 'GOT1', 't_depth': '100', 't_alt_count':'1', 't_af': '0.01'},
                    {'Hugo_Symbol': 'SOX9', 't_depth': '100', 't_alt_count':'0', 't_af': '0.0'}
                    ]
                self.assertEqual(mutations, expected_mutations)
    """
    # global settings for all test cases in the instance
    cwl_file = None # make sure to override this in subclasses before using the runner
    runner_args = dict(
        leave_outputs = False,
        leave_tmpdir = False,
        debug = False,
        parallel = False,
        js_console = False,
        print_command = False
        )

    # TODO: remove these from the object class! get them from fixtures.py instead
    DATA_SETS = DATA_SETS
    KNOWN_FUSIONS_FILE = KNOWN_FUSIONS_FILE
    IMPACT_FILE = IMPACT_FILE

    # these are the mappings of key:value pairs that should have the related keys removed
    # override this default setting when initializing the class instance, or just pass in
    # custom setting directly to the assertCWLDictEqual method
    related_keys = [
        # ("key", "value", ["badkey1", "badkey2", ...]),
        # removes 'size' and 'checksum' keys from the dict when 'basename' is 'report.html'
        ('basename', "report.html", ['size', 'checksum']),
        ('basename', "igv_report.html", ['size', 'checksum'])
        ]

    def setUp(self):
        """
        This gets automatically run before each test case

        Note
        ----
        This method will set up `self.preserve`, `self.tmpdir`, and `self.input`

        If USE_LSF is set, then we need to create the tmpdir in the pwd where its assumed to be accessible from the cluster
        """
        # put the CWL input data here; this will get dumped to a JSON file before executing tests
        self.input = {}

        # if we are using LSF then the tmpdir needs to be created in a location accessible by the whole cluster
        if USE_LSF:
            Path(TMP_DIR).mkdir(parents=True, exist_ok=True)
            self.tmpdir = mkdtemp(dir = TMP_DIR)
        else:
            self.tmpdir = mkdtemp()

        # prevent deletion of tmpdir after tests complete
        self.preserve = False
        if PRESERVE_TEST_DIR:
            self.preserve = True
            # if we are preserving the tmpdir we pretty much always want to know the path to it as well
            print(self.tmpdir)

    def tearDown(self):
        """
        This gets automatically run after each test case

        Note
        ----
        This method will delete `self.tmpdir` unless `self.preserve` is `True`
        """
        if not self.preserve:
            # remove the tmpdir upon test completion
            shutil.rmtree(self.tmpdir)

    def run_cwl(
        self,
        input: Dict = None,
        cwl_file: Union[str, CWLFile] = None,
        engine: str = "cwltool",
        *args, **kwargs) -> Tuple[Dict, str]:
        """
        Run the CWL specified for the test case

        Parameters
        ----------
        input: dict
            data dict to be used as input to the CWL
        cwl_file: str | CWLFile
            the CWLFile object or path to CWL file to run
        """
        # set default values
        if input is None:
            input = self.input
        if cwl_file is None:
            cwl_file = CWLFile(self.cwl_file)

        # override with value passed from env var
        if CWL_ENGINE:
            engine = CWL_ENGINE

        runner = CWLRunner(
            cwl_file = cwl_file,
            input = input,
            verbose = False,
            dir = self.tmpdir,
            testcase = self,
            engine = engine,
            *args, **self.runner_args, **kwargs)
            # debug = self.debug,
            # leave_tmpdir = self.leave_tmpdir,
            # leave_outputs = self.leave_outputs
        output_json, output_dir, output_json_file = runner.run()
        return(output_json, output_dir)

    def run_command(self, *args, **kwargs) -> Tuple[int, str, str]:
        """
        Run a shell command. Wrapper around :func:`~pluto.run_command`
        """
        returncode, proc_stdout, proc_stderr = run_command(*args, **kwargs)
        return(returncode, proc_stdout, proc_stderr)

    # wrappers around other functions in this module to reduce imports needed
    def write_table(self, *args, **kwargs) -> str:
        """
        Wrapper around :func:`~pluto.write_table`
        """
        filepath = write_table(*args, **kwargs)
        return(filepath)

    def read_table(self, input_file: str) -> List[ List[str] ]:
        """
        Simple loading of tabular lines in a file

        Parameters
        ----------
        input_file: str
            path to file

        Returns
        -------
        list
            a list of file lines split on whitespace
        """
        with open(input_file) as fin:
            lines = [ l.strip().split() for l in fin ]
        return(lines)

    def load_mutations(self, *args, **kwargs) -> Tuple[ List[str], List[Dict] ]:
        """
        Wrapper around :func:`~pluto.load_mutations`
        """
        comments, mutations = load_mutations(*args, **kwargs)
        return(comments, mutations)

    def dicts2lines(self, *args, **kwargs) -> List[ List[str] ]:
        """
        Wrapper around :func:`~pluto.dicts2lines`
        """
        lines = dicts2lines(*args, **kwargs)
        return(lines)

    def assertCWLDictEqual(
        self,
        d1: dict,
        d2: dict,
        bad_keys = ('nameext', 'nameroot'), # These keys show up inconsistently in Toil CWL output so just strip them out any time we see them
        related_keys = None, # mapping of key:value pairs that should trigger removal of other keys
        _print: bool = False,
        _printJSON: bool = False,
        *args, **kwargs):
        """
        wrapper around `unittest.TestCase.assertDictEqual` that can remove the keys for
        `nameext` and `nameroot`
        from dicts representing CWL cwltool / Toil JSON output
        before testing them for equality
        """
        if related_keys is None:
            related_keys = self.related_keys

        # if we are running with Toil then we need to remove the 'path' key
        # because thats just what Toil does idk why
        if CWL_ENGINE == "toil":
            bad_keys = [ *bad_keys, 'path' ]

        # copy the input dicts just to be safe
        # NOTE: this could backfire potentially, idk, watch out for big nested objects I guess
        d1_copy = deepcopy(d1)
        d2_copy = deepcopy(d2)
        clean_dicts(d1_copy, bad_keys = bad_keys, related_keys = related_keys)
        clean_dicts(d2_copy, bad_keys = bad_keys, related_keys = related_keys)
        if _print:
            print(d1_copy)
            print(d2_copy)
        if _printJSON:
            print(json.dumps(d1_copy, indent = 4))
            print(json.dumps(d2_copy, indent = 4))
        self.assertDictEqual(d1_copy, d2_copy, *args, **kwargs)
