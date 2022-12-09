import unittest
import os
from typing import Dict, Union, Tuple, List
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp
import shutil
from copy import deepcopy

# TODO: fix these imports somehow
try:
    from .settings import (
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
    from .cwlFile import CWLFile
    from .cwlRunner import CWLRunner
    from .util import (
        dicts2lines,
        write_table,
        clean_dicts,
        load_mutations,
        parse_header_comments,
        md5_obj
    )
    from .run import (
        run_command,
    )
except ImportError:
    from settings import (
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
    from cwlFile import CWLFile
    from cwlRunner import CWLRunner
    from util import (
        dicts2lines,
        write_table,
        clean_dicts,
        load_mutations,
        parse_header_comments,
        md5_obj
    )
    from .run import (
        run_command,
    )

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

    @classmethod
    def setUpClass(cls):
        """
        This gets run once after the class is imported, and before the unit test cases run

        Override this with methods that assign attributes back to cls
        e.g. set up a single pipeline to run in this method then set up test cases to evaluate its results

        NOTE: class gets imported once, but each test case gets executed in a separate instance of the class
        so we cannot assign values to instance "self", must be assigned to "cls"

        NOTE: dont think we can use super() here
        """
        pass
        # example;
        # need to make an instance of the test case class in order to run it
        # tc = cls()
        # tc.setUp()
        # output_json, output_dir = tc.setUpRun() # make a method to run the pipeline and return its outputs
        # store the outputs on the class itself
        # cls.tc = tc
        # cls.tmpdir = tc.tmpdir
        # cls.output_json = output_json
        # cls.output_dir = output_dir

    @classmethod
    def tearDownClass(cls):
        """
        Gets run
        """
        pass
        # example;
        # cls.tc.tearDown() # cls.rmtree(cls.tmpdir)

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
            PlutoTestCase.rmtree(self.tmpdir)

    @staticmethod
    def rmtree(path):
        shutil.rmtree(path)

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
        bad_keys = ('nameext', 'nameroot', 'streamable'), # These keys show up inconsistently in Toil CWL output so just strip them out any time we see them
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
    
    def assertMutationsHash(
        self,
        mutationsPath: str, # path to mutation file to test
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
            print(hash)
        else:
            self.assertEqual(hash, expected_hash, *args, **kwargs)

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
