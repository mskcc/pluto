from typing import Dict, Tuple

try:
    from plutoTestCase import PlutoTestCase
    from classes import NeedsOverrideError
except ImportError:
    from .classes import NeedsOverrideError
    from .plutoTestCase import PlutoTestCase


class Result:
    """
    """
    def __init__(self, output: Dict, expected: Dict, dir: str):
        self.output = output
        self.expected = expected
        self.dir = dir
    
    @classmethod
    def new(cls):
        return(cls({}, {}, ""))


class PlutoPreRunTestCase(PlutoTestCase):
    """
    A pluto test case that can run a CWL pipeline once during the testcase class setup, 
    then capture outputs from the workflow and save it so that
    it can be tested against in parallel downstream 'test_' methods
    instead of having to run the entire workflow in every 'test_' method
    This will save a ton of dev time when multiple assertions are needed to 
    verify the output of a workflow that takes a long time to finish,
    since we wont have to re-run the entire workflow repeatedly just to update all assertions
    """
    # these attributes and methods will be availabled under 'self' after initializing the class; 
    # override them with the ones specific to your test case

    # put a CWLFile object or path to a .cwl file here
    cwl_file = None
    
    # put setUpClass run results here
    res = Result.new()
    
    # put an instance of a PlutoTestCase here to use for setUp and tearDown of the tmpdir
    # we need to keep an initialized instance of PlutoTestCase in order to maintain the tmpdir
    # until all tests are completed, 
    # then we can remove it with the classmethod tearDownClass
    # otherwise the tmpdir gets automatically deleted at the end of ever 'test_' method
    tc = None

    # def setUp(self):
    #     """
    #     this method gets called for every 'test_' method
    #     """
    #     super().setUp()

    def setUpRun(self) -> Tuple[ Dict, str]:
        """
        place the 'run' method for each test case here
        this method should execute the CWL pipeline and return the output_json and output_dir objects
        """
        # EXAMPLE:
        # self.input = {
        #     "sample_groups": [sample_group1],
        #     "fillout_output_fname": 'output.maf',
        #     "ref_fasta": {"class": "File", "path": self.DATA_SETS['Proj_08390_G']['REF_FASTA']},
        # }
        # output_json, output_dir = self.run_cwl()
        # return(output_json, output_dir)
        raise NeedsOverrideError("PlutoPreRunTestCase.setUpRun() needs to be overriden in your custom class")
        return( {}, "" ) 
    
    def getExpected(self, output_dir: str) -> Dict:
        """
        """
        raise NeedsOverrideError("PlutoPreRunTestCase.getExpected() needs to be overriden in your custom class")
        return( {} )
    
    @classmethod
    def setUpClass(cls):
        """
        This method gets called ONCE before any 'test_' methods run
        This method needs to initialize an instance of the class to store for itself later for tearDown,
        then run the methods saved in setUpRun to execute the pipeline,
        then store the required pipeline outputs in the 'res' dict for use in 'test_' methods
        """
        # need to make an instance of the test case class in order to run it
        cls.tc = cls()
        cls.tc.setUp()
        output_json, output_dir = cls.tc.setUpRun()

        # store the outputs on the class itself
        cls.res = Result(output = output_json, expected = cls.tc.getExpected(output_dir), dir = output_dir)

    @classmethod
    def tearDownClass(cls):
        """
        This method gets called ONCE,
        after all 'test_' methods are complete
        This method needs to run the class instance tearDown method
        """
        cls.tc.tearDown()