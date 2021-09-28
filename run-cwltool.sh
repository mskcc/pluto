#!/bin/bash
# wrapper around running cwltool with some extra settings
set -eu
TIMESTAMP="$(date +%s)"
RUN_DIR="${PWD}/cwltool_runs/${TIMESTAMP}"
OUTPUT_DIR="${RUN_DIR}/output"
TMP_DIR="${RUN_DIR}/tmp"
LOG_FILE="${RUN_DIR}/stdout.log"
[ -e "${RUN_DIR}" ] && echo "ERROR: already exists; $RUN_DIR" && exit 1 || echo ">>> Running in ${RUN_DIR}"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$TMP_DIR"

set -x
cwltool \
--parallel \
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
