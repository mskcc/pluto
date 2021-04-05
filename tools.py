"""
Helper functions for running tests
"""
import sys
import os
import subprocess as sp
import csv
import json
from .settings import CWL_DIR, CWL_ARGS, TOIL_ARGS, DATA_SETS, KNOWN_FUSIONS_FILE, IMPACT_FILE
from collections import OrderedDict
import unittest
from tempfile import mkdtemp
import shutil
from pathlib import Path
import getpass

username = getpass.getuser()

class CWLRunner(object):
    """
    class for running a CWL File

    Usage:

    runner = CWLRunner(
        cwl_file = self.cwl_file,
        input = self.input,
        dir = self.dir,
        verbose = self.verbose)
    output_json, output_dir, output_json_file = runner.run()
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
                jobStore = self.jobStore
                )
        else:
            return()
        output_json_file = os.path.join(self.dir, "output.json")
        with open(output_json_file, "w") as fout:
            json.dump(output_json, fout, indent = 4)
        return(output_json, output_dir, output_json_file)



class CWLFile(os.PathLike):
    """
    wrapper class so I dont have to do

    from pluto.settings import CWL_DIR
    cwl_file = os.path.join(CWL_DIR, 'some.cwl')

    all the time
    """
    def __init__(self, path):
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

    Usage
    ------
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
    """Run the CWL with cwltool / cwl-runner"""
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
    Load the mutations from a file to use for testing
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
    create a list of line parts to pass for write_table;
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

class TableReader(object):
    """
    Handler for reading a table with comments

    Allows for parsing file attributes and rows without loading the whole file into memory

    NOTE: Input file must have column headers!

    Usage
    -----
    table_reader = TableReader(input_maf_file)
    comment_lines = table_reader.comment_lines
    fieldnames = table_reader.get_fieldnames()
    records = [ rec for rec in table_reader.read() ]
    """
    def __init__(self, filename, comment_char = '#', delimiter = '\t'):
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
    unittest.TestCase wrapper that includes a tmpdir
    Also, includes CWLRunner and the other helper functions from this module to make test case imports easier
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
        """this gets run for each test case"""
        self.preserve = False # save the tmpdir
        self.tmpdir = mkdtemp() # dir = THIS_DIR
        self.input = {} # put the CWL input data here

    def tearDown(self):
        """this gets run for each test case"""
        if not self.preserve:
            # remove the tmpdir upon test completion
            shutil.rmtree(self.tmpdir)

    def run_cwl(self, input = None, cwl_file = None):
        """run the CWL used in the test case"""
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
