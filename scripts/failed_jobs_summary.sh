#!/bin/bash
find . -maxdepth 2 -name toil.log -exec grep -E 'Job.*failed' {} \; | sed -e 's|/instance-[A-Za-z0-9_]*||g' -e 's|/[A-Za-z0-9] v[0-9]||g' -e 's| v[0-9]||g'| sort | uniq -c
