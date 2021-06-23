"""
Helper functions for running tests
"""
import sys
import os
import subprocess as sp
import csv
import json
try:
    from .settings import CWL_DIR, CWL_ARGS, TOIL_ARGS, DATA_SETS, KNOWN_FUSIONS_FILE, IMPACT_FILE
except ImportError:
    from settings import CWL_DIR, CWL_ARGS, TOIL_ARGS, DATA_SETS, KNOWN_FUSIONS_FILE, IMPACT_FILE
from collections import OrderedDict
import unittest
from tempfile import mkdtemp
import shutil
from pathlib import Path
import getpass
import hashlib

username = getpass.getuser()

class CWLRunner(object):
    """
    class for running a CWL File
    """
    def __init__(self,
        cwl_file, # str or CWLFile
        input, # pipeline input dict to be converted to JSON
        CWL_ARGS = CWL_ARGS,
        print_stdout = False,
        dir = None, # directory to run the CWL in and write output to
        output_dir = None, # directory to save output files to
        input_json_file = None, # path to write input JSON to if you already have one chosen
        input_is_file = False, # if the `input` arg should be treated as a pre-made JSON file and not a Python dict
        verbose = True,
        testcase = None,
        engine = "cwltool", # default engine is cwl-runner cwltool
        print_command = False,
        restart = False,
        jobStore = None,
        debug = False,
        leave_tmpdir = False,
        leave_outputs = False,
        parallel = False
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
                cwl_file = self.cwl_file,
                input = self.input,
                dir = self.dir,
                verbose = self.verbose)
            output_json, output_dir, output_json_file = runner.run()
        """
        self.cwl_file = cwl_file
        self.input = input
        self.CWL_ARGS = CWL_ARGS
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

        if dir is None:
            if engine == 'cwltool':
                dir = "cwltool_output"
            elif engine == 'toil':
                dir = "toil_output"
            else:
                dir = "pipeline_output"

        Path(os.path.abspath(dir)).mkdir(parents=True, exist_ok=True)
        self.dir = os.path.abspath(dir)

    def run(self):
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
                CWL_ARGS = self.CWL_ARGS,
                print_stdout = self.print_stdout,
                print_command = self.print_command,
                check_returncode = False,
                input_json_file = self.input_json_file,
                debug = self.debug,
                leave_tmpdir = self.leave_tmpdir,
                leave_outputs = self.leave_outputs,
                parallel = self.parallel,
                output_dir = self.output_dir,
                input_is_file = self.input_is_file
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
                input_is_file = self.input_is_file
                )
        else:
            return()
        output_json_file = os.path.join(self.dir, "output.json")
        with open(output_json_file, "w") as fout:
            json.dump(output_json, fout, indent = 4)
        return(output_json, output_dir, output_json_file)




class CWLFile(os.PathLike):
    """
    Wrapper class to locate the full path to a cwl file more conveniently
    """
    def __init__(self, path, CWL_DIR = CWL_DIR):
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
        self.path = os.path.join(CWL_DIR, path)
    def __str__(self):
        return(self.path)
    def __repr__(self):
        return(self.path)
    def __fspath__(self):
        return(self.path)





def run_command(args, testcase = None, validate = False, print_stdout = False):
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
    testcase, # 'self' in the unittest.TestCase instance
    tmpdir, # dir where execution is taking place and files are staged & written
    input_json, # CWL input data
    cwl_file, # CWL file to run
    CWL_ARGS = CWL_ARGS, # default cwltool args to use
    print_stdout = False,
    print_command = False,
    check_returncode = True,
    input_json_file = None,
    debug = False,
    leave_tmpdir = False,
    leave_outputs = False,
    parallel = False,
    output_dir = None,
    input_is_file = False # if the `input_json` is actually a path to a pre-existing JSON file
    ):
    """
    Run the CWL with cwltool / cwl-runner

    Returns
    -------
    dict:
        output data dictionary loaded from CWL stdout JSON
    str:
        path to the `output` directory from the CWL workflow
    """
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
        CWL_ARGS = [ *CWL_ARGS, '--leave-outputs' ]
    if leave_tmpdir:
        CWL_ARGS = [ *CWL_ARGS, '--leave-tmpdir' ]
    if debug:
        CWL_ARGS = [ *CWL_ARGS, '--debug' ]
    if parallel:
        print(">>> Running cwl-runner with 'parallel'; make sure all Singularity containers are pre-cached!")
        # if the containers are not already all pre-pulled then it can cause issues with parallel jobs all trying to pull the same container to the same filepath
        CWL_ARGS = [ *CWL_ARGS, '--parallel' ]

    command = [
        "cwl-runner",
        *CWL_ARGS,
        "--outdir", output_dir,
        "--tmpdir-prefix", tmp_dir,
        "--cachedir", cache_dir,
        cwl_file, input_json_file
        ]
    if print_command:
        print(">>> cwl-runner command:")
        print(' '.join([ str(c) for c in  command ]) )

    returncode, proc_stdout, proc_stderr = run_command(command)


    if print_stdout:
        print(proc_stdout)

    if returncode != 0:
        print(proc_stderr)

    if check_returncode:
        testcase.assertEqual(returncode, 0)

    output_json = json.loads(proc_stdout)
    return(output_json, output_dir)

def run_cwl_toil(
        input_data,
        cwl_file,
        run_dir,
        output_dir = None,
        workDir = None,
        jobStore = None,
        tmpDir = None,
        logFile = None,
        input_json_file = None,
        print_command = False,
        restart = False,
        TOIL_ARGS = TOIL_ARGS,
        input_is_file = False # if the `input_json` is actually a path to a pre-existing JSON file
        ):
    """
    Run a CWL using Toil
    """
    run_dir = os.path.abspath(run_dir)


    # if we are not restarting, jobStore should not already exist
    if not restart:
        if not jobStore:
            jobStore = os.path.join(run_dir, "jobstore")
        if os.path.exists(jobStore):
            print(">>> ERROR: Job store already exists; ", jobStore)
            sys.exit(1)
        TOIL_ARGS = [ *TOIL_ARGS, '--jobStore', jobStore ]

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
        TOIL_ARGS = [ *TOIL_ARGS, '--restart', '--jobStore', jobStore ]

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
        *TOIL_ARGS,
        "--logFile", logFile,
        "--outdir", output_dir,
        '--workDir', workDir,
        '--tmpdir-prefix', tmpDirPrefix,
        cwl_file, input_json_file
        ]


    if print_command:
        print(">>> toil-cwl-runner command:")
        print(' '.join([ str(c) for c in  command ]) )

    returncode, proc_stdout, proc_stderr = run_command(command)

    try:
        output_data = json.loads(proc_stdout)
        return(output_data, output_dir)

    # if you cant decode the JSON stdout then it did not finish correctly
    except json.decoder.JSONDecodeError:
        print(proc_stdout)
        print(proc_stderr)
        raise


def parse_header_comments(filename, comment_char = '#'):
    """
    Parse a file with comments in its header to return the comments and the line number to start reader from

    Parameters
    ----------
    filename: str
        path to input file
    comment_char: str
        comment character


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
                comments.append(line.strip())
                start_line += 1
    return(comments, start_line)

def load_mutations(filename):
    """
    Load the mutations from a tabular .maf file to use for testing
    """
    comments, start_line = parse_header_comments(filename)
    with open(filename) as fin:
        while start_line > 0:
            next(fin)
            start_line -= 1
        reader = csv.DictReader(fin, delimiter = '\t')
        mutations = [ row for row in reader ]
    return(comments, mutations)

def write_table(tmpdir, filename, lines, delimiter = '\t', filepath = None):
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
    """
    if not filepath:
        filepath = os.path.join(tmpdir, filename)
    with open(filepath, "w") as f:
        for line in lines:
            line_str = delimiter.join(line) + '\n'
            f.write(line_str)
    return(filepath)

def dicts2lines(dict_list, comment_list = None):
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

def md5_file(filename):
    """
    Get md5sum of a file
    """
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
    hash = file_hash.hexdigest()
    return(hash)





class TableReader(object):
    """
    Handler for reading a table with comments

    Allows for parsing file attributes and rows without loading the whole file into memory

    Note
    ----
    Input file must have column headers!
    """
    def __init__(self, filename, comment_char = '#', delimiter = '\t'):
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
        self.comments, self.start_line = parse_header_comments(filename, comment_char = self.comment_char)
        self.comment_lines = [ c + '\n' for c in self.comments ]

    def get_reader(self, fin):
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

    def get_fieldnames(self):
        """
        returns the list of fieldnames for the table
        """
        with open(self.filename,'r') as fin:
            reader = self.get_reader(fin)
            return(reader.fieldnames)

    def read(self):
        """
        iterable to get the record rows from the table, skipping the comments
        """
        with open(self.filename,'r') as fin:
            reader = self.get_reader(fin)
            for row in reader:
                yield(row)

    def count(self):
        """
        Return the total number of records in the table
        """
        num_records = 0
        for _ in self.read():
            num_records += 1
        return(num_records)








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
    DATA_SETS = DATA_SETS
    KNOWN_FUSIONS_FILE = KNOWN_FUSIONS_FILE
    IMPACT_FILE = IMPACT_FILE
    runner_args = dict(
        leave_outputs = False,
        leave_tmpdir = False,
        debug = False,
        parallel = False
        )

    def setUp(self):
        """This gets automatically run before each test case"""
        self.preserve = False # save the tmpdir
        self.tmpdir = mkdtemp() # dir = THIS_DIR
        self.input = {} # put the CWL input data here

    def tearDown(self):
        """This gets automatically run after each test case"""
        if not self.preserve:
            # remove the tmpdir upon test completion
            shutil.rmtree(self.tmpdir)

    def run_cwl(self, input = None, cwl_file = None):
        """
        Run the CWL specified for the test case

        Parameters
        ----------
        input: dict
            data dict to be used as input to the CWL
        cwl_file: str | CWLFile
            the CWLFile object or path to CWL file to run
        """
        if input is None:
            input = self.input
        if cwl_file is None:
            cwl_file = CWLFile(self.cwl_file)
        runner = CWLRunner(
            cwl_file = cwl_file,
            input = input,
            verbose = False,
            dir = self.tmpdir,
            testcase = self,
            **self.runner_args)
            # debug = self.debug,
            # leave_tmpdir = self.leave_tmpdir,
            # leave_outputs = self.leave_outputs
        output_json, output_dir, output_json_file = runner.run()
        return(output_json, output_dir)

    def run_command(self, *args, **kwargs):
        """run a CLI command"""
        returncode, proc_stdout, proc_stderr = run_command(*args, **kwargs)
        return(returncode, proc_stdout, proc_stderr)

    # wrappers around other functions in this module to reduce imports needed
    def write_table(self, *args, **kwargs):
        filepath = write_table(*args, **kwargs)
        return(filepath)

    def read_table(self, input_file):
        """simple loading of tabular lines in a file"""
        with open(input_file) as fin:
            lines = [ l.strip().split() for l in fin ]
        return(lines)

    def load_mutations(self, *args, **kwargs):
        comments, mutations = load_mutations(*args, **kwargs)
        return(comments, mutations)

    def dicts2lines(self, *args, **kwargs):
        lines = dicts2lines(*args, **kwargs)
        return(lines)
