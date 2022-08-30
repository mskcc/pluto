"""
Put settings to use for the tests in here for easier access

Override these settings with environment variables:

PRINT_COMMAND=true KEEP_TMP=true CWL_ENGINE=toil LARGE_TESTS=true python3 test_tools.py

"""
import os
# TODO: fix these imports somehow
try:
    from classes import (
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
except ModuleNotFoundError:
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

quiet_mode = SuppressStartupMessages(os.environ.get('QUIET', False))

# enable execution of very large tests used in some test cases;
ENABLE_LARGE_TESTS = EnableLargeTests(os.environ.get('LARGE_TESTS', False))
if ENABLE_LARGE_TESTS:
    if not quiet_mode:
        print(">>> Enabling execution of large test cases...")

# use this flag for enabling the huge workflow test cases for Jenkins CI, etc
ENABLE_INTEGRATION_TESTS = EnableIntergrationTests(os.environ.get('INTEGRATION_TESTS', False))
if ENABLE_INTEGRATION_TESTS:
    if not quiet_mode:
        print(">>> Enabling execution of large integration test cases...")

# use LSF with Toil
USE_LSF = UseLSF(os.environ.get('USE_LSF', None))

# whether Toil or cwltool should be used
CWL_ENGINE = CWLEngine(os.environ.get('CWL_ENGINE', None))

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
KEEP_TMP = KeepTmp(os.environ.get('KEEP_TMP', False))

# if the CWL runner command should be printed before running it
PRINT_COMMAND = PrintCommand(os.environ.get('PRINT_COMMAND', False))

# print the name of each test before it starts running
PRINT_TESTNAME = PrintTestName(os.environ.get('PRINT_TESTNAME', False))

# retrieve the run stats for Toil
TOIL_STATS = ToilStats(os.environ.get('STATS', False))

PRINT_STATS = PrintToilStats(os.environ.get('PRINT_STATS', False))

SAVE_STATS = SaveToilStats(os.environ.get('SAVE_STATS', False))

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
    '--disableCaching', 'True',
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




# ~~~~~~~~~~ #
# TODO: Move these settings back to pluto-cwl repo! Make sure they're not also used in helix_filters_01 repo though

# location on the filesystem for static fixtures
FIXTURES_DIR = os.environ.get('FIXTURES_DIR', '/juno/work/ci/helix_filters_01/fixtures')
FACETS_SNPS_VCF = os.environ.get('FACETS_SNPS_FILE', '/juno/work/ci/resources/genomes/GRCh37/facets_snps/dbsnp_137.b37__RmDupsClean__plusPseudo50__DROP_SORT.vcf')
KNOWN_FUSIONS_FILE = os.path.join(REF_DIR, "known_fusions_at_mskcc.txt")
IMPACT_FILE=os.environ.get('IMPACT_file', '/work/ci/helix_filters_01/reference_data/gene_lists/all_IMPACT_genes.tsv')

ARGOS_VERSION_STRING = os.environ.get('ARGOS_VERSION_STRING', '2.x') # TODO: deprecate this
IS_IMPACT = os.environ.get('IS_IMPACT', "True") # TODO: deprecate this
PORTAL_FILE = os.environ.get('PORTAL_FILE', 'data_mutations_extended.txt') # TODO: deprecate this
PORTAL_CNA_FILE = os.environ.get('PORTAL_CNA_FILE', 'data_CNA.txt') # TODO: deprecate this

REF_FASTA = os.environ.get('REF_FASTA', '/juno/work/ci/resources/genomes/GRCh37/fasta/b37.fasta')
MICROSATELLITES_LIST = os.environ.get("MICROSATELLITES_LIST", "/work/ci/resources/request_files/msisensor/microsatellites.list")
# $ md5sum /work/ci/resources/request_files/msisensor/microsatellites.list
# dc982a3bfe1e33b201b99a8ebf3acd61  /work/ci/resources/request_files/msisensor/microsatellites.list
# $ wc -l /work/ci/resources/request_files/msisensor/microsatellites.list
# 33422661 /work/ci/resources/request_files/msisensor/microsatellites.list

DATA_SETS = {
    "Proj_08390_G": { # full sample Argos output
        "DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G"),
        "MAF_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "maf"),
        "BAM_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "bam"),
        # "SNP_PILEUP_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "snp_pileup"),
        "FACETS_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "facets"),
        "FACETS_SUITE_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "facets-suite"),
        "INPUTS_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "inputs"),
        "QC_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "qc"),
        "targets_list": "/juno/work/ci/resources/roslin_resources/targets/HemePACT_v4/b37/HemePACT_v4_b37_targets.ilist",
        "analyst_file": "Proj_08390_G.muts.maf", # TODO: deprecate this
        "analysis_gene_cna_file": "Proj_08390_G.gene.cna.txt", # TODO: deprecate this
        "MAF_FILTER_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "maf_filter"),
        "SNP_PILEUP_DIR": os.path.join(FIXTURES_DIR, "Proj_08390_G", "snp-pileup"),
        'REF_FASTA': REF_FASTA,
        'microsatellites_file': MICROSATELLITES_LIST
    },
    "Proj_1": { # same as Proj_08390_G but both filenames and file contents have been scrubbed; results in different file md5's
        "MAF_DIR": os.path.join(FIXTURES_DIR, "Proj_1", "maf"),
        "BAM_DIR": os.path.join(FIXTURES_DIR, "Proj_1", "bam"),
        "FACETS_DIR": os.path.join(FIXTURES_DIR, "Proj_1", "facets"),
        "FACETS_SUITE_DIR": os.path.join(FIXTURES_DIR, "Proj_1", "facets-suite"),
        "QC_DIR": os.path.join(FIXTURES_DIR, "Proj_1", "qc"),
        "INPUTS_DIR": os.path.join(FIXTURES_DIR, "Proj_1", "inputs"),
        'REF_FASTA': REF_FASTA,
        "targets_list": "/juno/work/ci/resources/roslin_resources/targets/HemePACT_v4/b37/HemePACT_v4_b37_targets.ilist",
    },
    "demo":{ # small subset of samples on a full project
        "DIR": os.path.join(FIXTURES_DIR, "demo"),
        "MAF_DIR": os.path.join(FIXTURES_DIR, "demo", "maf"),
        "BAM_DIR": os.path.join(FIXTURES_DIR, "demo", "bam"),
        "QC_DIR": os.path.join(FIXTURES_DIR, "demo", "qc"),
        "INPUTS_DIR": os.path.join(FIXTURES_DIR, "demo", "inputs"),
        "SNP_PILEUP_DIR": os.path.join(FIXTURES_DIR, "demo", "snp-pileup"),
        "FACETS_DIR": os.path.join(FIXTURES_DIR, "demo", "facets"),
        "targets_list": "/juno/work/ci/resources/roslin_resources/targets/HemePACT_v4/b37/HemePACT_v4_b37_targets.ilist",
        'microsatellites_file': os.path.join(FIXTURES_DIR, "demo", "microsatellites", 'microsatellites.head500000.list'),
        # $ md5sum microsatellites.head500000.list
        # aa0126e6a916ec82a2837989458918b3  microsatellites.head500000.list
        'REF_FASTA': REF_FASTA
    },
    # dataset selected for use with fillout since it has pooled normals
    "07618_AG": {
        "DIR": os.path.join(FIXTURES_DIR, "07618_AG"),
        "BAM_DIR": os.path.join(FIXTURES_DIR, "07618_AG", "bam"),
        "MAF_DIR": os.path.join(FIXTURES_DIR, "07618_AG", "maf")
    },
    "Fillout01": {
        "DIR": os.path.join(FIXTURES_DIR, "Fillout01"),
        "BAM_DIR": os.path.join(FIXTURES_DIR, "Fillout01", "bam"),
        "MAF_DIR": os.path.join(FIXTURES_DIR, "Fillout01", "maf"),
        "VCF_DIR": os.path.join(FIXTURES_DIR, "Fillout01", "vcf"),
        "OUTPUT_DIR": os.path.join(FIXTURES_DIR, "Fillout01", "output")
    }
}
