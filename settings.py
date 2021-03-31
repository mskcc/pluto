"""
Put settings to use for the tests in here for easier access
"""
import os

# disable execution of very large tests;
ENABLE_LARGE_TESTS = os.environ.get('LARGE_TESTS') == "True"
# $ LARGE_TESTS=True python3 tests
# tag large test cases with:
# @unittest.skipIf(ENABLE_LARGE_TESTS != True, "is a large test")
if ENABLE_LARGE_TESTS:
    print(">>> Enabling execution of large test cases...")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CWL_DIR = os.path.join(os.path.dirname(THIS_DIR), "cwl") # ../cwl
REF_DIR = os.path.join(os.path.dirname(THIS_DIR), "ref") # ../ref
EXAMPLES_DIR = os.path.join(os.path.dirname(THIS_DIR), "examples") # ../examples

# common args to be included in all cwltool invocations
CWL_ARGS = [
    "--preserve-environment", "PATH",
    "--preserve-environment", "SINGULARITY_CACHEDIR",
    "--singularity"
]
TOIL_ARGS = [
    '--singularity', # run with Singularity instead of Docker
    '--batchSystem', 'lsf', '--disableCaching', 'True', # use LSF on the HPC to submit jobs
    '--disable-user-provenance', '--disable-host-provenance',
    '--preserve-entire-environment', # need to propagate the env vars for Singularity, etc., into the HPC jobs
    '--retryCount', '1',
    '--maxLocalJobs', '500', # run up to 500 jobs at once; not actually "local", this includes HPC jobs
    '--statePollingWait', '10', # check available jobs every 10 seconds instead of after every job is submitted
    '--clean', 'onSuccess', # deletion of the jobStore # {always,onError,never,onSuccess}
    '--cleanWorkDir', 'onSuccess' # deletion of temporary worker directory # {always,onError,never,onSuccess}
]

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
    "Proj_08390_G": {
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
    "demo":{
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
    }
}
