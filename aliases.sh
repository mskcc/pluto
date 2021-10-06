# aliases to quickly evaluate pipeline pass/fail
# examples;

# for i in $(find . -maxdepth 2 -type f -name toil.log); do grep -q "Finished toil run successfully." $i && echo succes $i || echo failed $i ; done
# for i in $(find . -maxdepth 2 -type f -name toil.log); do grep -q "Finished toil run successfully." $i && s $(dirname $i) || f $(dirname $i) ; done


s () {
    (
    set -ux
    touch "${1}/success"
    [ -f "${1}/fail" ] && rm -f "${1}/fail" || :
    )
}

f () {
    (
    set -ux
    touch "${1}/fail"
    [ -f "${1}/success" ] && rm -f "${1}/success" || :
    )

}

t () {
    (
    set -u
    tail -100 "${1}/toil.log"
    )
}
