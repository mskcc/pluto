"""
Put settings to use for the tests in here for easier access

Override these settings with environment variables:

PRINT_COMMAND=true KEEP_TMP=true CWL_ENGINE=toil LARGE_TESTS=true python3 test_tools.py

"""
import os
from .classes import (
    CWLEngine,
    UseLSF,
    EnableLargeTests,
    EnableIntergrationTests,
    KeepTmp,
    PrintCommand,
    PrintTestName,
    SuppressStartupMessages,
    ToilStats,
    PrintToilStats,
    SaveToilStats
    )

quiet_mode = SuppressStartupMessages(os.environ.get('QUIET', "False"))

# enable execution of very large tests used in some test cases;
ENABLE_LARGE_TESTS = EnableLargeTests(os.environ.get('LARGE_TESTS', "False"))
if ENABLE_LARGE_TESTS:
    if not quiet_mode:
        print(">>> Enabling execution of large test cases...")

# use this flag for enabling the huge workflow test cases for Jenkins CI, etc
ENABLE_INTEGRATION_TESTS = EnableIntergrationTests(os.environ.get('INTEGRATION_TESTS', "False"))
if ENABLE_INTEGRATION_TESTS:
    if not quiet_mode:
        print(">>> Enabling execution of large integration test cases...")

# use LSF with Toil
USE_LSF = UseLSF(os.environ.get('USE_LSF', "False"))

# whether Toil or cwltool should be used
CWL_ENGINE = CWLEngine(os.environ.get('CWL_ENGINE', "None"))
CWL_DEFAULT_ENGINE = CWLEngine("cwltool")

# the location of this file
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# need to set some default locations for some dir's based on the standard submodule structure
# TODO: make env vars for this
CWL_DIR = os.path.join(os.path.dirname(THIS_DIR), "cwl") # ../cwl
REF_DIR = os.path.join(os.path.dirname(THIS_DIR), "ref") # ../ref
EXAMPLES_DIR = os.path.join(os.path.dirname(THIS_DIR), "examples") # ../examples

# location to run workflows, mostly needed for use with LSF, this needs to be accessible cluster-wide
# This is only used when running with Toil or LSF
TMP_DIR = os.environ.get("TMP_DIR", None)
# if no dir was passed then use the pwd
if not TMP_DIR:
    TMP_DIR = os.path.join(os.getcwd(), "tmp")

# if the tmpdir used in PlutoTestCase should be preserved (not deleted) after tests complete
KEEP_TMP = KeepTmp(os.environ.get('KEEP_TMP', "False"))

# if the CWL runner command should be printed before running it
PRINT_COMMAND = PrintCommand(os.environ.get('PRINT_COMMAND', "False"))

# print the name of each test before it starts running
PRINT_TESTNAME = PrintTestName(os.environ.get('PRINT_TESTNAME', "False"))

# retrieve the run stats for Toil
TOIL_STATS = ToilStats(os.environ.get('STATS', "False"))

PRINT_STATS = PrintToilStats(os.environ.get('PRINT_STATS', "False"))

SAVE_STATS = SaveToilStats(os.environ.get('SAVE_STATS', "False"))

# dir to save stats files in
STATS_DIR = os.environ.get("STATS_DIR", None)
if not STATS_DIR:
    STATS_DIR = os.path.join(os.getcwd(), "stats")

if PRINT_STATS or SAVE_STATS:
    TOIL_STATS.value = True

# common args to be included in all cwltool invocations
CWL_ARGS = [
    "--preserve-environment", "PATH",
    "--preserve-environment", "SINGULARITY_CACHEDIR",
    "--singularity"
]
TOIL_ARGS = [
    '--singularity', # run with Singularity instead of Docker
    '--disable-user-provenance', '--disable-host-provenance',
    '--disableCaching', # 'True', # NOTE: in Toil 5.4.2 you use '--disableCaching True' but in 5.7.1 you use just '--disableCaching'
    '--realTimeLogging',
    # need to propagate the env vars for Singularity, etc., into the HPC jobs
    '--preserve-environment', 'PATH', 'TMPDIR', 'TOIL_LSF_ARGS', 'SINGULARITY_PULLDIR', 'SINGULARITY_CACHEDIR',
    'SINGULARITYENV_LC_ALL', 'PWD',  'SINGULARITY_DOCKER_USERNAME', 'SINGULARITY_DOCKER_PASSWORD',
    '--retryCount', '1',
    '--statePollingWait', '10', # check available jobs every 10 seconds instead of after every job is submitted
    '--doubleMem',
    '--defaultMemory', '8G',
    '--maxCores', '16',
    '--maxDisk', '128G',
    '--maxMemory', '256G',
    '--not-strict'
]


# need to explictly set Toil's handling of temp dir deletions because by default it will delete all tmp dirs and we pretty much always need to keep them because otherwise its impossible to debug anything
# default settings
TOIL_CLEAN_SETTINGS = {
    'clean':'onSuccess', # deletion of the jobStore # {always,onError,never,onSuccess}
    'cleanWorkDir': 'onSuccess' # deletion of temporary worker directory # {always,onError,never,onSuccess}
}

# make sure TMP_DIR's dont get deleted if we wanted to keep tmp
if KEEP_TMP:
    TOIL_CLEAN_SETTINGS['clean'] = 'never'
    TOIL_CLEAN_SETTINGS['cleanWorkDir'] = 'never'

# https://toil.readthedocs.io/en/3.10.1/running/cli.html#stats saves /stats under the jobstore dir for use with `toil stats <jobstore>`
# NOTE: `toil stats` reports memory in Kibibytes (default) or Mebibytes ("human readable")
if TOIL_STATS:
    TOIL_CLEAN_SETTINGS['clean'] = 'never'
    TOIL_CLEAN_SETTINGS['cleanWorkDir'] = 'never'
    TOIL_ARGS = [
        *TOIL_ARGS,
        '--stats'
        ]

TOIL_ARGS = [
    *TOIL_ARGS,
    '--clean', TOIL_CLEAN_SETTINGS['clean'],
    '--cleanWorkDir', TOIL_CLEAN_SETTINGS['cleanWorkDir']
]



# use LSF on the HPC to submit jobs
if USE_LSF:
    TOIL_ARGS = [
        *TOIL_ARGS,
        '--batchSystem', 'lsf',
        '--maxLocalJobs', '50', # number of parallel jobs to run; not actually "local", this includes HPC jobs
        '--coalesceStatusCalls',
        '--disableProgress'
         ]
