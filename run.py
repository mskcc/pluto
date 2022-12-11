import os
import sys
import json
import unittest
import subprocess as sp
from pathlib import Path
from typing import List, Dict, Tuple, Union

# TODO: fix these imports somehow
try:
    from .settings import (
        CWL_ARGS,
        TOIL_ARGS,
    )
    from .cwlFile import CWLFile
except ImportError:
    from settings import (
        CWL_ARGS,
        TOIL_ARGS,
    )
    from cwlFile import CWLFile

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
