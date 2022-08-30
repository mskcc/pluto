"""
Helper functions for running tests
"""
import sys
import os
import subprocess as sp
import csv
import json
import gzip
from datetime import datetime
# TODO: fix these imports somehow
try:
    from .settings import (
        CWL_ARGS,
        TOIL_ARGS,
        DATA_SETS,
        KNOWN_FUSIONS_FILE,
        IMPACT_FILE,
        USE_LSF,
        TMP_DIR,
        KEEP_TMP,
        CWL_ENGINE,
        PRINT_COMMAND,
        PRINT_TESTNAME,
        TOIL_STATS,
        PRINT_STATS,
        SAVE_STATS,
        STATS_DIR
    )
    from .settings import CWL_DIR as _CWL_DIR
except ImportError:
    from settings import (
        CWL_ARGS,
        TOIL_ARGS,
        DATA_SETS,
        KNOWN_FUSIONS_FILE,
        IMPACT_FILE,
        USE_LSF,
        TMP_DIR,
        KEEP_TMP,
        CWL_ENGINE,
        PRINT_COMMAND,
        PRINT_TESTNAME,
        TOIL_STATS,
        PRINT_STATS,
        SAVE_STATS,
        STATS_DIR
    )
    from settings import CWL_DIR as _CWL_DIR
from collections import OrderedDict
import unittest
from tempfile import mkdtemp, mkstemp
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
        print_stdout: bool = False, # whether stdout from the CWL workflow should be printed to console
        dir: str = None, # directory to run the CWL in and write output to
        output_dir: str = None, # directory to save output files to
        input_json_file: str = None, # path to write input JSON to if you already have one chosen
        input_is_file: bool = False, # if the `input` arg should be treated as a pre-made JSON file and not a Python dict
        verbose: bool = True, # include descriptive messages in console stdout when running CWL
        testcase: unittest.TestCase = None, # object to use when making assertions when running as part of a unit test
        engine: str = "cwltool", # run the CWL with cwl-runner (`"cwltool"`) or Toil (`"toil"`)
        print_command: bool = False, # print the fully evaluated command to console before running
        restart: bool = False, # enable "restart" or "resume" functionality when running the CWL workflow
        jobStore: str = None, # Toil job store to use when restarting a pipeline
        debug: bool = False, # whether to include the `--debug` arg with the CWL runner command for extra console output in case of error and debugging
        leave_tmpdir: bool = False, # do not delete the tmp dir after the CWL workflow finishes
        leave_outputs: bool = False, # do not delete the output dir after completion
        parallel: bool = False, # run workflow jobs in parallel; NOTE: make sure all Singularity containers are cached first or it will break
        js_console: bool = False,
        print_stderr: bool = False,
        use_cache: bool = True,
        toil_stats: bool = None # if follow-up steps should be taken to collect Toil run stats; assumes that TOIL_ARGS has been updated for including the --stats flag which creates required output in the jobstore
        ):
        """
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
        self.toil_stats = toil_stats
        self.toil_stats_dict = {}

        # override some settings from env vars
        if PRINT_COMMAND:
            self.print_command = PRINT_COMMAND
        if TOIL_STATS:
            self.toil_stats = TOIL_STATS

        if dir is None:
            if engine == 'cwltool':
                dir = "cwltool_output"
            elif engine == 'toil':
                dir = "toil_output"
            else:
                dir = "pipeline_output"
            # if engine == 'cwltool':
            #     dir = "cwltool_output"
            # elif engine == 'toil':
            #     dir = "toil_output"
            # else:
            #     dir = "pipeline_output"

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
            output_json, output_dir, jobStore = run_cwl_toil(
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
            # NOTE: returned jobStore may be different from self.jobStore if self.jobStore was never passed to runner during init
            if self.toil_stats:
                self.toil_stats_dict = self.get_toil_stats(jobStore)
        else:
            # TODO: what should we do in the case where the engine doesnt match one of the above??
            # This should probably raise an error
            raise InvalidEngine(">>> ERROR: invalid engine provided: {}. Try 'cwltool' or 'toil'".format(self.engine))

        output_json_file = os.path.join(self.dir, "output.json")
        with open(output_json_file, "w") as fout:
            json.dump(output_json, fout, indent = 4)
        return(output_json, output_dir, output_json_file)

    def get_toil_stats(self, jobStore: str) -> Dict:
        """
        # NOTE: `toil stats` reports memory in Kibibytes (default) or Mebibytes ("human readable")
        """
        command = ["toil", "stats", "--raw", jobStore]
        returncode, proc_stdout, proc_stderr = run_command(command)
        stats = json.loads(proc_stdout)
        return(stats)

    # def format_toil_stats(self):
    #     d = {
    #     'total_run_time': self.toil_stats_dict.get('total_run_time'),
    #     }
    #     if self.toil_stats_dict.get('worker'):
    #         d['total_number'] = self.toil_stats_dict['worker'].get('total_number')
















def run_command(
    args: List[str], # a list of shell args to execute
    testcase: unittest.TestCase = None, # a test case instance for making assertions
    validate: bool = False, # whether to check that the exit code was 0; requires `testcase`
    print_stdout: bool = False) -> Tuple[int, str, str]:
    """
    Helper function to run a shell command easier

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
    """
    if CLI_ARGS is None:
        CLI_ARGS = CWL_ARGS

    if not input_is_file:
        # the input_json is a Python dict that needs to be dumped to file
        if not input_json_file:
            input_json_file = os.path.join(tmpdir, "input.json")
        with open(input_json_file, "w") as json_out:
            json.dump(input_json, json_out, indent = 4)
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
        print(">>> Running cwl-runner with 'parallel'; make sure all Singularity containers are pre-cached or it will break!")
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
        input_data: Dict, # this is supposed to be a Python dict which will be written to JSON file but sometimes it can instead be a pre-made JSON file path if you also pass in input_is_file=True
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
        ) -> Tuple[Dict, str, str]: # [outputDict, outputDirPath]
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
            json.dump(input_data, json_out, indent = 4)
    else:
        # input_json is a pre-existing JSON file
        input_json_file = input_data

    if output_dir is None:
        # /run-1/output
        output_dir = os.path.join(run_dir, "output")
    if workDir is None:
        # /run-1/work
        workDir = os.path.join(run_dir, "work")
    if logFile is None:
        # /run-1/toil.log
        logFile = os.path.join(run_dir, "toil.log")
    if tmpDir is None:
        # /run-1/tmp
        tmpDir = os.path.join(run_dir, "tmp")
        # tmpDir = os.path.join('/scratch', username) <- dont do this anymore, set it via TMP_DIR env var instead

    # /run-1/tmp/tmpabcxyz
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
        return(output_data, output_dir, jobStore)

    # if you cant decode the JSON stdout then it did not finish correctly
    except json.decoder.JSONDecodeError:
        print(proc_stdout)
        print(proc_stderr)
        raise


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
    maxDiff = None
    # global settings for all test cases in the instance
    cwl_file = None # make sure to override this in subclasses before using the runner
    runner_args = dict(
        leave_outputs = False,
        leave_tmpdir = False,
        debug = True,
        parallel = False,
        js_console = True, #False,
        # use_cache = False, # need to set this for some samples fillout workflows that break on split_vcf_to_mafs
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
        self.start_time = datetime.now()
        self.test_label = "{}.{}".format(type(self).__name__, self._testMethodName)
        # put the CWL input data here; this will get dumped to a JSON file before executing tests
        self.input = {}

        if PRINT_TESTNAME:
            print("\n>>> starting test: {}".format(self.test_label))

        # if we are using LSF then the tmpdir needs to be created in a location accessible by the whole cluster
        if USE_LSF:
            Path(TMP_DIR).mkdir(parents=True, exist_ok=True)
            self.tmpdir = mkdtemp(dir = TMP_DIR)
        # also Toil tmp dir grows to massive sizes so do not use /tmp for it because it fills up
        elif CWL_ENGINE.toil:
            Path(TMP_DIR).mkdir(parents=True, exist_ok=True)
            self.tmpdir = mkdtemp(dir = TMP_DIR)
        # if a TMP_DIR was passed in the environment variable
        elif TMP_DIR:
            Path(TMP_DIR).mkdir(parents=True, exist_ok=True)
            self.tmpdir = mkdtemp(dir = TMP_DIR)
        else:
            self.tmpdir = mkdtemp()

        # prevent deletion of tmpdir after tests complete
        self.preserve = False
        if KEEP_TMP:
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
        self.stop_time = datetime.now()
        self.time_elapsed = self.stop_time - self.start_time

        # if we were using PRINT_TESTNAME then we will want to know when the test completed as well
        if PRINT_TESTNAME:
            print("\n>>> stopping test: {} ({})".format(self.test_label, self.time_elapsed))

        # remove the tmpdir upon test completion
        if not self.preserve:
            shutil.rmtree(self.tmpdir)

    def run_cwl(
        self,
        input: Dict = None,
        cwl_file: Union[str, CWLFile] = None,
        engine: str = "cwltool", # TODO: need better handling for the default value here, try to get it from CWL_ENGINE instead
        allow_empty_input: bool = False, # don't print a warning if we know its OK for the input dict to be empty
        *args, **kwargs) -> Tuple[Dict, str]:
        """
        Run the CWL specified for the test case

        NOTE: Make sure to only call this one time per test case!! Otherwise jobstore dirs may persist and break subsequent runs
        """
        # set default values
        if input is None:
            input = self.input
        if cwl_file is None:
            cwl_file = CWLFile(self.cwl_file)

        # print a warning if self.input was empty; this is usually an oversight during test dev
        if not input and not allow_empty_input:
            print(">>> WARNING: empty input passed to run_cwl() by test: ", self.test_label)

        # override with value passed from env var
        if CWL_ENGINE != engine:
            engine = CWL_ENGINE

        # save a file to the run dir to mark that this test has started running
        filename = "{}.run".format(self.test_label)
        run_marker_file = os.path.join(self.tmpdir, filename)
        with open(run_marker_file, "w") as fout:
            fout.write(str(self.start_time))

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

        # if Toil run stats were retrieved, either save or print them as requested
        if runner.toil_stats_dict:
            if PRINT_STATS:
                print("\n>>> {} stats:\n{}".format(self.test_label, runner.toil_stats_dict)) # runner.format_toil_stats

            if SAVE_STATS:
                Path(STATS_DIR).mkdir(parents=True, exist_ok=True)
                filename = "{}.json".format(self.test_label)
                stats_output_file = os.path.join(STATS_DIR, filename)
                with open(stats_output_file, "w") as fout:
                    json.dump(runner.toil_stats_dict, fout, indent = 4)

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

    def mkstemp(self, dir: str = None, *args, **kwargs) -> str:
        """
        Make a temporary file
        https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp
        https://stackoverflow.com/questions/38436987/python-write-in-mkstemp-file
        """
        if dir is None:
            dir = self.tmpdir
        fd, path = mkstemp(dir = dir, *args, **kwargs) # fileDescriptor, filePath
        return(path)

    def jsonDumps(self, d):
        """
        """
        print(json.dumps(d, indent = 4))

    def getAllSampleFileValues(
        self,
        filepaths: List[str], # list of tables to read values from
        value_fieldname: str, # field in each table to read values from
        sample_fieldname: str = "SAMPLE_ID" # field in each table to read sample ID from
        ) -> Dict:
        """
        Collect the values from a list of filepaths for a value per sample and return a single dict with all samples' values
        """
        values = {}
        for filepath in filepaths:
            table_reader = TableReader(filepath)
            records = [ rec for rec in table_reader.read() ]
            for record in records:
                sample_id = record[sample_fieldname]
                values[sample_id] = record[value_fieldname]
        return(values)

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
        Compare the JSON-style CWL output dicts

        wrapper around `unittest.TestCase.assertDictEqual` that can remove the keys for
        `nameext` and `nameroot`
        from dicts representing CWL cwltool / Toil JSON output
        before testing them for equality
        """
        if related_keys is None:
            related_keys = self.related_keys

        # if we are running with Toil then we need to remove the 'path' key
        # because thats just what Toil does idk why
        if CWL_ENGINE.toil:
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

    def assertNumMutationsHash(
        self,
        mutationsPath: str, # path to mutation file to test
        expected_num: int, # number of mutations that should be in the file
        expected_hash: str, # md5 of the Python loaded mutation list object
        strip: bool = True, # need this to remove variable mutation fields
        _print: bool = False, # don't run tests, just print the results (for dev and debug)
        *args, **kwargs
        ):
        """
        wrapper for asserting that the number of mutations and the md5 of the Python mutation object match the expected values
        Use this with `strip` for removal of mutation keys that can be variable and change md5
        """
        comments, mutations = self.load_mutations(mutationsPath, strip = strip)
        hash = md5_obj(mutations)

        if _print:
            print(len(mutations), hash)
        else:
            self.assertEqual(len(mutations), expected_num, *args, **kwargs)
            self.assertEqual(hash, expected_hash, *args, **kwargs)

    def assertMutFileContains(
        self,
        filepath: str,
        expected_comments: List[str],
        expected_mutations: List[str],
        comments_identical: bool = False,
        mutations_identical: bool = False,
        identical: bool = False,
        *args, **kwargs
        ):
        """
        Check that mutation file contains expected header and mutation contents
        """
        if identical:
            comments_identical = True
            mutations_identical = True
        comments, mutations = self.load_mutations(filepath)

        if comments_identical:
            self.assertEqual(expected_comments, comments)
        else:
            for comment in expected_comments:
                message = "Comment '{}' is not in comments list: {}".format(comment, comments)
                self.assertTrue(comment in comments, message, *args, **kwargs)

        if mutations_identical:
            self.assertEqual(expected_mutations, mutations)
        else:
            for mut in expected_mutations:
                message = "Mutation missing from file: {}".format(mut)
                self.assertTrue(mut in mutations, message, *args, **kwargs)

    def assertCompareMutFiles(self,
        filepath1: str,
        filepath2: str,
        muts_only: bool = False,
        compare_len: bool = False,
        *args, **kwargs
        ):
        """
        """
        if not muts_only:
            comments1, mutations1 = self.load_mutations(filepath1)
            self.assertMutFileContains(filepath = filepath2, expected_comments = comments1, expected_mutations = mutations1)
        else:
            _, mutations1 = self.load_mutations(filepath1)
            self.assertMutFileContains(filepath = filepath2, expected_comments = [], expected_mutations = mutations1)

        if compare_len:
            _, mutations2 = self.load_mutations(filepath2)
            len1 = len(mutations1)
            len2 = len(mutations2)
            message = "File {} has a different number of mutations from file {} ({} vs {})".format(filepath1, filepath2, len1, len2)
            self.assertEqual(len1, len2, *args, **kwargs)


    def assertNumMutations(
        self,
        filepath: str,
        expected_num: int,
        *args, **kwargs
        ):
        """
        Assertion for the number of mutations in a file
        """
        comments, mutations = self.load_mutations(filepath)
        self.assertEqual(len(mutations), expected_num, *args, **kwargs)

    def assertEqualNumMutations(
        self,
        mutationFiles: List[str], # several mutation file paths
        expectedMutFile: str, # single mutation file path to compare number of muts against
        *args, **kwargs):
        """
        wrapper for asserting that the number of mutations across all mutation files in each group is equal
        """
        numMuts = []
        for filepath in mutationFiles:
            comments, mutations = self.load_mutations(filepath)
            numMutations = len(mutations)
            numMuts.append(numMutations)
        sumMuts = sum(numMuts)

        comments, expected_mutations = self.load_mutations(expectedMutFile)
        sumExpectedMuts = len(expected_mutations)

        self.assertEqual(sumMuts, sumExpectedMuts, *args, **kwargs)

    def assertMutFieldContains(
        self,
        filepath: str, # path to mutation file
        fieldname: str, # path to mutation .maf field to check
        values: List[str], # list of desired values in the field
        containsAll: bool = False, # only the provided values are allowed
        *args, **kwargs
        ):
        """
        Test that the set of all values in a column of the mutation maf file contains all the desired values
        """
        wantedValuesSet = set(values)
        comments, mutations = self.load_mutations(filepath)
        allValues = set()
        for mut in mutations:
            allValues.add(mut[fieldname])
        missingWanted = wantedValuesSet - allValues
        message = "values {} missing from field {}; wanted: {} got: {}".format(missingWanted, fieldname, wantedValuesSet, allValues)
        self.assertEqual(len(missingWanted), 0, message, *args, **kwargs)

        if containsAll:
            unwantedValues = allValues - wantedValuesSet
            message = "got unwanted values in field {}: {} : wanted values: {}".format(fieldname, unwantedValues, wantedValuesSet)
            self.assertEqual(len(unwantedValues), 0, message, *args, **kwargs)
    
    def assertMutFieldDoesntContain(
        self,
        filepath: str,
        fieldname: str,
        values: List[str],
        *args, **kwargs
        ):
        """
        """
        unwantedValues = set(values)
        comments, mutations = self.load_mutations(filepath)
        allValues = set()
        for mut in mutations:
            allValues.add(mut[fieldname])

        presentValues = []
        for value in unwantedValues:
            if value in allValues:
                presentValues.append(value)
        
        wanted = []
        message = "got unwanted values {} in field {}".format(presentValues, fieldname)
        self.assertEqual(wanted, presentValues, message, *args, **kwargs)



    def assertHeaderEquals(
        self,
        filepath: str,
        expected_headers: List[str],
        *args, **kwargs
        ):
        """
        Assertion for validating the header fields of a tab separated file
        """
        with open(filepath) as f:
            header = next(f)
        header_parts = header.split() # split on whitespace
        self.assertEqual(header_parts, expected_headers, *args, **kwargs)

    def assertPortalCommentsEquals(
        self,
        filepath: str,
        expected_comments: List[List[str]],
        ignoreOrder: bool = False,
        transpose: bool = False,
        *args, **kwargs
        ):
        """
        """
        table_reader = TableReader(filepath)
        comments = table_reader.comment_lines # list of strings that looks like this; [ '#Header1\tHeader\n', ... ]
        # fieldnames = table_reader.get_fieldnames()
        # records = [ rec for rec in table_reader.read() ]
        comment_parts = []
        for comment in comments:
            comment = comment.lstrip("#")
            parts = comment.split()
            comment_parts.append(parts)

        # use this to make viewing the diff easier
        if transpose:
            comment_parts = list(map(list, zip(*comment_parts)))

        # exact comparison
        if not ignoreOrder:
            message = "comment_parts are not the same as expected_comments"
            self.assertEqual(comment_parts, expected_comments, message)

        # compare irrespective of order of columns\
        # NOTE: maybe do not use this because it makes it impossible to enforce the contents of the file ... hmm...
        else:
            # TODO: consider making this a set operation
            message = "len comment_parts ({}) not equal to len expected_comments ({})".format(len(comment_parts), len(expected_comments))
            self.assertEqual(len(comment_parts), len(expected_comments), message)
            for i, _ in enumerate(expected_comments):
                message = "len comment_parts ({}) not equal to len expected_comments ({})".format(len(comment_parts), len(expected_comments))
                self.assertEqual(len(comment_parts[i]), len(expected_comments[i]), message)
            for i, comments in enumerate(expected_comments):
                for comment in comments:
                    message = "comment {} not in comment_parts".format(comment)
                    self.assertTrue(comment in comment_parts[i], message)

    def assertMutHeadersContain(
        self,
        filepath: str,
        expected_headers: List[str],
        *args, **kwargs
        ):
        """
        Check that mutation file headers contain expected values
        """
        expected_headersSet = set(expected_headers)
        comments, mutations = self.load_mutations(filepath)
        colnames = mutations[0].keys()
        colnamesSet = set(colnames) # in case older versions of Python did not return a set type
        missingWanted = expected_headersSet - colnamesSet
        message = "Expected columns {} missing from mutation file".format(missingWanted)
        self.assertEqual(len(missingWanted), 0, message, *args, **kwargs)
        # for colname in expected_headers:
        #     message = "Column label '{}' is missing in mutation file".format(colname)
        #     self.assertTrue(colname in colnames, message, *args, **kwargs)

    def assertMutHeadersAllowed(
        self,
        filepath: str,
        allowed_headers: List[str],
        *args, **kwargs
        ):
        """
        Check that only allowed header columns are present in the mutation file
        """
        comments, mutations = self.load_mutations(filepath)
        colnames = mutations[0].keys()
        for key in mutations[0].keys():
            message = "Columns {} not allowed in mutation file".format(key)
            self.assertTrue(key in allowed_headers, message, *args, **kwargs)

    def assertFileLinesEqual(self, filepath: str, expected_lines: List[str]):
        """
        """
        with open(filepath) as fin:
            output_lines = [ line.strip() for line in fin ]
        self.assertEqual(output_lines, expected_lines)

    def assertSampleValues(
        self,
        filepath: str,
        expected_values: Dict,
        value_fieldname: str,
        sample_fieldname: str = "SAMPLE_ID"
        ):
        """
        Check that samples in the file have expected values
        Assumes samples are unique
        """
        table_reader = TableReader(filepath)
        records = [ rec for rec in table_reader.read() ]
        values = {}
        for record in records:
            sample_id = record[sample_fieldname]
            values[sample_id] = record[value_fieldname]
        self.assertDictEqual(values, expected_values)
