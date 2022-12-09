import os
import json
import unittest
from pathlib import Path
from typing import Dict, Tuple, Union

# TODO: fix these imports somehow
try:
    from .settings import (
        PRINT_COMMAND,
        TOIL_STATS,
    )
    from .cwlFile import CWLFile
    from .run import (
        run_command,
        run_cwl,
        run_cwl_toil
    )
except ImportError:
    from settings import (
        PRINT_COMMAND,
        TOIL_STATS,
    )
    from cwlFile import CWLFile
    from run import (
        run_command,
        run_cwl,
        run_cwl_toil
    )


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

