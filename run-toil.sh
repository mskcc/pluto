#!/bin/bash
# wrapper around running Toil with some extra settings
# you need to source env.sh first for some of this to work; https://github.com/mskcc/pluto-cwl/blob/2742b41ab2946326e45c094cd5468d454b5e5b64/env.juno.sh#L46
# example usage;
# $ . env.juno.sh toil
# $ ./run-toil.sh cwl/some_workflow.cwl input.json

# need these to avoid Dockerhub rate limit issues with pipelines; get it from env.sh
[ $SINGULARITY_DOCKER_USERNAME ] || echo ">>> WARNING: SINGULARITY_DOCKER_USERNAME is not set, HPC jobs might break!"
[ $SINGULARITY_DOCKER_PASSWORD ] || echo ">>> WARNING: SINGULARITY_DOCKER_PASSWORD is not set, HPC jobs might break!"

set -eu

# fail fast if Toil is not loaded
which toil-cwl-runner 1>/dev/null

# files and dirs for the pipeline run
TIMESTAMP="$(date +%s)"
RUN_DIR="${PWD}/toil_runs/${TIMESTAMP}"
OUTPUT_DIR="${RUN_DIR}/output"
TMP_DIR="${RUN_DIR}/tmp"
WORK_DIR="${RUN_DIR}/work"
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

# avoid race condition where two scripts start at the same time; add sleep backoff so they dont collide in a loop
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

# save a copy of the environment
env > "${ENV_FILE}"
echo "$$" > "${PID_FILE}"
hostname > "${HOST_FILE}"

# save copies of input arg files
for i in $@; do
if [ -f "$i" ]; then
cp "$i" "${RUN_DIR}/"
fi
done

# record start time
date +%s > "${TIMESTART_FILE}"

# turn these off because we need to track failures
set +e
set +u
# turn this on because we need to track command used and pipeline failures through tee pipe
set -xo pipefail

# run in background subprocess so we can capture the set -x stderr message showing the full command executed
# capture the exit code for the pipeline when its done
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
--maxLocalJobs 100 \
--cleanWorkDir onSuccess \
--clean onSuccess \
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

# re-raise the pipeline exit code
exit $exit_code






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
