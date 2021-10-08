#!/bin/bash
# some runs were made before I started copying over the labeled input json so need to copy it over so we have consistent run labels
INPUT_JSON="$(readlink -f ../input.demo_small_2_samples.json)"
for i in $(find . -maxdepth 2 -type f -name toil.log); do
    run_dir="$(readlink -f $(dirname $i))"
    (
    cd $run_dir
    if ls input*json 1>/dev/null 2>/dev/null; then
        :
    else
        cp "${INPUT_JSON}" "${run_dir}/"
    fi
    )

    (
    cd $run_dir
    if ls input.json 1>/dev/null 2>/dev/null; then
        echo $run_dir
    fi
    )
done
