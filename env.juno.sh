#!/bin/bash
# environment settings for use on Juno HPC cluster
# copied from https://github.com/mskcc/pluto-cwl/blob/master/env.juno.sh

# USAGE: . env.juno.sh <target>

arg="${1:-None}"

case $arg in
    cwltool)
        module load singularity/3.3.0
        module load python/3.7.1
        module load cwl/cwltool
        ;;

    *)
        echo "unrecognized target called"
        # exit 1
        ;;
esac
