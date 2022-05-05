#!/bin/bash
# wrapper around running cwltool with some extra settings
# example usage;
# $ . env.juno.sh toil
# $ ./run-cwltool.sh cwl/some_workflow.cwl input.json


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

# make sure we fail fast if there's an error
set -eu
TIMESTAMP="$(date +%s)"
DEFAULT_RUN_DIR="${PWD}/cwltool_runs/${TIMESTAMP}"

# allow for override from command line;
# $ RUN_DIR=foo ./run-cwltool.sh ...
RUN_DIR="${RUN_DIR:-$DEFAULT_RUN_DIR}"
LOG_FILE="${RUN_DIR}/stdout.log"

OUTPUT_DIR="${RUN_DIR}/output"

TMP_DIR="${RUN_DIR}/tmp"

[ -e "${RUN_DIR}" ] && echo "ERROR: already exists; $RUN_DIR" && exit 1 || echo ">>> Running in ${RUN_DIR}"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$TMP_DIR"

set -x
cwltool \
--preserve-environment PATH \
--preserve-environment SINGULARITY_CACHEDIR \
--singularity \
--leave-tmpdir \
--debug \
--outdir "$OUTPUT_DIR" \
--tmpdir-prefix "$TMP_DIR" \
$@ 2>&1 | tee "${LOG_FILE}"

echo ">>> done: ${RUN_DIR}"

# some extra args to try
# --parallel
# --js-console
# --cachedir

# NOTE: --parallel causes random failures too often so do not use it by default!
