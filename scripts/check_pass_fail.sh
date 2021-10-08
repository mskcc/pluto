#!/bin/bash

# $ ./check_pass_fail.sh | cut -f1-2 | sort | uniq -c

for i in $(find . -maxdepth 2 -type f -name toil.log); do
    run_dir=$(basename $(dirname $i))
    run_dir_path="$(readlink -f $(dirname $i))"
    result=""
    input_json=""

    if [ -e "${run_dir_path}/success" ]; then
        result="success"
    elif [ -e "${run_dir_path}/fail" ]; then
        result="fail"
    fi

    if ls ${run_dir_path}/input*json 1>/dev/null 2>/dev/null; then
        input_json="$(find "${run_dir_path}" -maxdepth 1 -type f -name "input*json" -exec basename {} \;)"
    fi
    printf "${result}\t${input_json}\t${run_dir}\n"
done
