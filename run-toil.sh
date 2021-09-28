#!/bin/bash
# wrapper around running Toil with some extra settings
# you need to source env.sh first for some of this to work

# need these to avoid Dockerhub rate limit issues with pipelines; get it from env.sh
[ $SINGULARITY_DOCKER_USERNAME ] || echo ">>> WARNING: SINGULARITY_DOCKER_USERNAME is not set, HPC jobs might break!"
[ $SINGULARITY_DOCKER_PASSWORD ] || echo ">>> WARNING: SINGULARITY_DOCKER_PASSWORD is not set, HPC jobs might break!"

set -eu

# NOTE: do I still need to do this??
unset SINGULARITY_CACHEDIR

TIMESTAMP="$(date +%s)"
RUN_DIR="${PWD}/toil_runs/${TIMESTAMP}"
OUTPUT_DIR="${RUN_DIR}/output"
TMP_DIR="${RUN_DIR}/tmp"
WORK_DIR="${RUN_DIR}/work"
JOB_STORE="${RUN_DIR}/jobstore"
STDOUT_LOG_FILE="${RUN_DIR}/stdout.log"
LOG_FILE="${RUN_DIR}/toil.log"
[ -e "${RUN_DIR}" ] && echo "ERROR: already exists; $RUN_DIR" && exit 1 || echo ">>> Running in ${RUN_DIR}"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$TMP_DIR"
mkdir -p "$WORK_DIR"

# mkdir -p "$JOB_STORE" # don't create this ahead of time
# if we are not restarting, jobStore should not already exist
# --restart --jobStore "${JOB_STORE}" \
# if we are restarting, jobStore needs to exist

set -x

( toil-cwl-runner \
--logFile "${LOG_FILE}" \
--outdir "${OUTPUT_DIR}" \
--workDir "${WORK_DIR}" \
--tmpdir-prefix "${TMP_DIR}" \
--jobStore "${JOB_STORE}" \
--singularity \
--batchSystem lsf --disableCaching True \
--disable-user-provenance \
--disable-host-provenance \
--preserve-entire-environment \
--statePollingWait 10 \
--maxLocalJobs 500 \
$@ ) 2>&1 | tee "${STDOUT_LOG_FILE}"

echo ">>> done: ${RUN_DIR}"

# some extra args that might be needed;
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
