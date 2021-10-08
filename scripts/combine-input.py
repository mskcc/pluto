#!/usr/bin/env python3

# simple script to use for trying to combine samples from two helix filter (pluto-cwl) input.json files
# methods should be mostly generic for other input.json files, 
# but stuff like correctly merging str fields and handling for int's will need some kind of special handling

import sys
import os
import json

args = sys.argv[1:]
input1 = args.pop()
input2 = args.pop()

output_data = dict()

with open(input1) as fin:
    data1 = json.load(fin)

with open(input2) as fin:
    data2 = json.load(fin)

for key in data1.keys():
    # concatenate strings, '.' should be a pipeline-safe join char
    if isinstance(data1[key], str):
        # if its a number, then use the first value as-is
        # if data1[key].isdigit():
        #     output_data[key] = data1[key]

        # we know this value should be an int, but trying to parse int's breaks for other ID's that are all numerics so just handle this special case
        if key == 'assay_coverage':
            output_data[key] = data1[key]
        else:
            new_str = '.'.join([data1[key], str(data2[key])])
            output_data[key] = new_str

    # if its null then keep it as null unless the other one has a value
    if data1[key] is None:
        if data2[key] is None:
            output_data[key] = None
        else:
            output_data[key] = data2[key]

    # concatenate lists
    if isinstance(data1[key], list):
        new_list = []
        for item in data1[key]:
            new_list.append(item)
        for item in data2[key]:
            new_list.append(item)
        output_data[key] = new_list

    # if its a File then use the first one
    # if its a File with embedded contents then we need special handling to concat the files
    if isinstance(data1[key], dict):
        if "contents" not in data1[key]:
            output_data[key] = data1[key]

        # file has "contents" embedded as one giant string; need to split lines and parse
        else:
            contents1 = data1[key]["contents"].split('\n')
            contents2 = data2[key]["contents"].split('\n')
            # discard first line of second file; the header line
            discard_header = contents2.pop(0)
            new_contents = []
            for line in contents1:
                new_contents.append(line)
            for line in contents2:
                new_contents.append(line)
            # merge it back to a single string
            # NOTE: there should not be a trailing newline... I think?
            new_contents = '\n'.join(new_contents)
            output_data[key] = data1[key]
            output_data[key]["contents"] = new_contents

print(json.dumps(output_data, indent = 4))
