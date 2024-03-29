#!/bin/bash
# wrapper around running Toil with some extra settings
# you need to source env.sh first for some of this to work; https://github.com/mskcc/pluto-cwl/blob/2742b41ab2946326e45c094cd5468d454b5e5b64/env.juno.sh#L46
# example usage;
# $ . env.juno.sh toil
# $ ./run-toil.sh cwl/some_workflow.cwl input.json
# $ for i in $(seq 1 5); do ./run-toil.sh cwl/workflow_with_facets.cwl input.json; done
# $ LOCAL=True ./run-toil.sh cwl/workflow_with_facets.cwl input.json


# ~~~~~ ENV VARS NEEDED TO KEEP PIPELINE RUNS FROM BREAKING ~~~~~ #
# get these from ` . env.juno.sh toil`
# need these to avoid Dockerhub rate limit issues with pipelines; get it from env.sh
[ $SINGULARITY_DOCKER_USERNAME ] || echo ">>> WARNING: SINGULARITY_DOCKER_USERNAME is not set, HPC jobs might break!"
[ $SINGULARITY_DOCKER_PASSWORD ] || echo ">>> WARNING: SINGULARITY_DOCKER_PASSWORD is not set, HPC jobs might break!"

# need this in order for Toil to find pre-cached Singularity containers without re-pulling them all
[ $CWL_SINGULARITY_CACHE ] || echo ">>> WARNING: CWL_SINGULARITY_CACHE is not set, HPC jobs and parallel scatter jobs might break!"

# SINGULARITY_PULLDIR is the same location as CWL_SINGULARITY_CACHE ;
# SINGULARITY_PULLDIR gets used automatically by Singularity but can cause undesired results when cwltool tries to pull images
# not to be confused with SINGULARITY_PULLFOLDER ... https://github.com/common-workflow-language/cwltool/blob/a3cc4fcd29792342832b3571b27096a18b41d252/cwltool/singularity.py#L134
[ $SINGULARITY_PULLDIR ] && echo ">>> WARNING: SINGULARITY_PULLDIR is set, if Toil tries to pull Singularity containers they might get saved to the wrong place!"


# Need this to prevent R UTF.8 parse errors that make libraries not found
# export SINGULARITYENV_LC_ALL=en_US.UTF-8
[ $SINGULARITYENV_LC_ALL ] || echo ">>> WARNING: SINGULARITYENV_LC_ALL is not set, some R and Facets jobs might break!"

# Need this for extra LSF HPC settings; e.g.
# export TOIL_LSF_ARGS='-sla FOOBAR'
[ "$TOIL_LSF_ARGS" ] || echo ">>> WARNING: TOIL_LSF_ARGS is not set, HPC jobs might take a long time to run!"

# NOTE: Might also need these; if using them, make sure all dirs exist ahead of time!
# export SINGULARITY_CACHEDIR=/path/to/cache
# export SINGULARITY_TMPDIR=$SINGULARITY_CACHEDIR/tmp
# export SINGULARITY_PULLDIR=$SINGULARITY_CACHEDIR/pull
# export CWL_SINGULARITY_CACHE=$SINGULARITY_PULLDIR
# ~~~~~~~~~~~~~~~ #


# ~~~~~ SETUP FOR AN ISOLATED SELF-CONTAINED HEADACHE-FREE PIPELINE RUN ~~~~~ #
# make sure we fail fast if there's an error
set -eu

# fail fast if Toil is not loaded
which toil-cwl-runner 1>/dev/null

# files and dirs for this current pipeline run instance
TIMESTAMP="$(date +%s)"

DEFAULT_RUN_DIR="${PWD}/toil_runs/${TIMESTAMP}"

# allow for override from command line;
# $ RUN_DIR=foo ./run-cwltool.sh ...
RUN_DIR="${RUN_DIR:-$DEFAULT_RUN_DIR}"
# RUN_DIR="${PWD}/toil_runs/${TIMESTAMP}"

DEFAULT_TMP_DIR="${RUN_DIR}/tmp"
TMP_DIR="${TMP_DIR:-$DEFAULT_TMP_DIR}"

DEFAULT_WORK_DIR="${RUN_DIR}/work"
WORK_DIR="${WORK_DIR:-$DEFAULT_WORK_DIR}"

LOG_DIR="${RUN_DIR}/logs"
OUTPUT_DIR="${RUN_DIR}/output"
JOB_STORE="${RUN_DIR}/jobstore"
STDOUT_LOG_FILE="${RUN_DIR}/stdout.log"
LOG_FILE="${RUN_DIR}/toil.log"
SUCCESS_FILE="${RUN_DIR}/success"
FAIL_FILE="${RUN_DIR}/fail"
ENV_FILE="${RUN_DIR}/env"
TIMESTART_FILE="${RUN_DIR}/start"
TIMESTOP_FILE="${RUN_DIR}/stop"
EXIT_CODE_FILE="${RUN_DIR}/exit_code"
PID_FILE="${RUN_DIR}/pid"
HOST_FILE="${RUN_DIR}/hostname"
TOIL_VERSION_FILE="${RUN_DIR}/toil_version"
STATS_JSON="${RUN_DIR}/stats.json"
CLUSTERSTATS_JSON="${RUN_DIR}/clusterstats.json"


# avoid race condition where two run-toil.sh scripts start at the same time;
# add sleep backoff so they dont collide in a loop
SLEEP_TIME="$(shuf -i 1-10 -n 1)"
[ -e "${RUN_DIR}" ] && \
echo "ERROR: already exists; ${RUN_DIR}, waiting ${SLEEP_TIME}s before exiting" && \
sleep "${SLEEP_TIME}" && \
exit 1 || \
echo ">>> Running in ${RUN_DIR}"


# start setting up the run dir
mkdir -p "$OUTPUT_DIR"
mkdir -p "$TMP_DIR"
mkdir -p "$WORK_DIR"
mkdir -p "$LOG_DIR"


# save a copy of the environment
env > "${ENV_FILE}"
echo "$$" > "${PID_FILE}"
hostname > "${HOST_FILE}"
toil-cwl-runner --version > "${TOIL_VERSION_FILE}"


# save copies of input arg files
for i in $@; do
if [ -f "$i" ]; then
cp "$i" "${RUN_DIR}/"
fi
done


# if cwl dir exists, save copy of that as well since there might be more changes throughout the pipeline
[ -d cwl ] && cp -a cwl "${RUN_DIR}/" || :
# also save copy of pip install requirements file in case we had changed Toil install stack (it would be saved there)
[ -f requirements.txt ] && cp -a requirements.txt "${RUN_DIR}/" || :
# save copy of this script
cp "$0" "${RUN_DIR}/"


# record start time
date +%s > "${TIMESTART_FILE}"
# ~~~~~~~~~~~~~~~ #



# ~~~~~ START RUNNING THE PIPELINE ~~~~~ #
# turn these off because we need to track failures
set +e
set +u
# turn this on because we want to track the final command executed and pipeline failures through tee pipe
set -xo pipefail

# env var to run without LSF
LOCAL="${LOCAL:-False}"
if [ "${LOCAL}" == "False" ] ; then
    LSF_COMMAND=" --batchSystem lsf "
else
    LSF_COMMAND=""
fi

# env var to run with stats
STATS="${STATS:-}"
if [ "${STATS}" != "False" ] ; then
    STATS_COMMAND=" --cleanWorkDir never --clean never  --stats "
else
    STATS_COMMAND=" --cleanWorkDir onSuccess --clean onSuccess "
fi

# run in background subprocess so we can capture the set -x stderr message showing the full command executed
# capture the exit code for the pipeline when its done
# NOTE: try to mimic most of the args used here; https://github.com/mskcc/ridgeback/blob/ae51a1a38e8247e3ff1bd1c0791ba4515f9dc6c3/submitter/toil_submitter/toil_jobsubmitter.py#L209-L254
# TODO: also try using these; some of them broke Toil last time I tried though but its shown as used in prod
# --writeLogs "${LOG_DIR}" \
# --realTimeLogging \
# --coalesceStatusCalls \ # TODO: Get this working!! it greatly reduces size of logs but it broke on some dev Toil branches
( nice toil-cwl-runner \
--logFile "${LOG_FILE}" \
--outdir "${OUTPUT_DIR}" \
--workDir "${WORK_DIR}" \
--tmpdir-prefix "${TMP_DIR}" \
--jobStore "${JOB_STORE}" \
--singularity --disableCaching True $LSF_COMMAND \
--disable-user-provenance \
--disable-host-provenance \
--preserve-environment \
PATH TMPDIR TOIL_LSF_ARGS SINGULARITY_PULLDIR SINGULARITY_CACHEDIR \
SINGULARITYENV_LC_ALL PWD  SINGULARITY_DOCKER_USERNAME SINGULARITY_DOCKER_PASSWORD \
--statePollingWait 10 \
--maxLocalJobs 100 \
--doubleMem \
--defaultMemory 8G \
--maxCores 16 \
--maxDisk 128G \
--maxMemory 256G \
--not-strict \
--coalesceStatusCalls \
--writeLogs "${LOG_DIR}" \
--clusterStats "${CLUSTERSTATS_JSON}" \
--realTimeLogging $STATS_COMMAND \
$@ ) 2>&1 | tee "${STDOUT_LOG_FILE}" ; exit_code="$?"

set +x

# check if the run was successful
if [ $exit_code -ne 0 ]; then
    touch "${FAIL_FILE}"
    echo ">>> failed: ${RUN_DIR}"
else
    touch "${SUCCESS_FILE}"
    echo ">>> done: ${RUN_DIR}"
fi

# record time stop and final exit code
date +%s > "${TIMESTOP_FILE}"
echo "${exit_code}" > "${EXIT_CODE_FILE}"

# try to get some toil stats that should have been saved
if [ "${STATS}" != "" ]; then
  toil stats --raw "${JOB_STORE}" > "${STATS_JSON}"
  rm -rf "${JOB_STORE}"
  rm -rf "${TMP_DIR}"
  rm -rf "${WORK_DIR}"
fi

# re-raise the pipeline exit code
exit $exit_code








# ~~~~~~~ extra notes ~~~~~~ #
# some extra Toil args that might be needed;
# --preserve-environment PATH TMPDIR TOIL_LSF_ARGS SINGULARITY_CACHEDIR SINGULARITY_TMPDIR SINGULARITY_PULLDIR PWD \
# --maxLocalJobs 500 \
# TOIL_ARGS = [
#     '--singularity', # run with Singularity instead of Docker
#     '--batchSystem', 'lsf', '--disableCaching', 'True', # use LSF on the HPC to submit jobs
#     '--disable-user-provenance', '--disable-host-provenance',
#     '--preserve-entire-environment', # need to propagate the env vars for Singularity, etc., into the HPC jobs
#     '--retryCount', '1',
#     '--maxLocalJobs', '500', # run up to 500 jobs at once; not actually "local", this includes HPC jobs
#     '--statePollingWait', '10', # check available jobs every 10 seconds instead of after every job is submitted
#     '--clean', 'onSuccess', # deletion of the jobStore # {always,onError,never,onSuccess}
#     '--cleanWorkDir', 'onSuccess' # deletion of temporary worker directory # {always,onError,never,onSuccess}
# ]
# mkdir -p "$JOB_STORE" # don't create this ahead of time
# if we are not restarting, jobStore should not already exist
# --restart --jobStore "${JOB_STORE}" \
# if we are restarting, jobStore needs to exist

# --stats               Records statistics about the toil workflow to be used
#                       by 'toil stats'.
# --clean {always,onError,never,onSuccess}
#                       Determines the deletion of the jobStore upon
#                       completion of the program. Choices: ['always',
#                       'onError', 'never', 'onSuccess']. The --stats option
#                       requires information from the jobStore upon completion
#                       so the jobStore will never be deleted with that flag.
#                       If you wish to be able to restart the run, choose
#                       'never' or 'onSuccess'. Default is 'never' if stats is
#                       enabled, and 'onSuccess' otherwise.
# --cleanWorkDir {always,onError,never,onSuccess}
#                       Determines deletion of temporary worker directory upon
#                       completion of a job. Choices: ['always', 'onError',
#                       'never', 'onSuccess']. Default = always. WARNING: This
#                       option should be changed for debugging only. Running a
#                       full pipeline with this option could fill your disk
#                       with excessive intermediate data.
# --clusterStats [CLUSTERSTATS]
#                       If enabled, writes out JSON resource usage statistics
#                       to a file. The default location for this file is the
#                       current working directory, but an absolute path can
#                       also be passed to specify where this file should be
#                       written. This options only applies when using scalable
#                       batch systems.
