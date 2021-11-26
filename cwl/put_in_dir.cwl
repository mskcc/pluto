#!/usr/bin/env cwl-runner

# tool for copying a File or Directory into a subdir
# NOTE: This appears to have issues copying a dir under Linux??
cwlVersion: v1.0

class: CommandLineTool
baseCommand: [ "bash", "run.sh" ]
requirements:
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entryname: run.sh
        entry: |-
          output_directory_name="${ return inputs.output_directory_name; }"
          mkdir "\${output_directory_name}"
          input_item="${ return inputs.item.path; }"
          cp -r "\${input_item}" "\${output_directory_name}/"

inputs:
  output_directory_name: string
  item:
    type:
      - File
      - Directory

outputs:
  directory:
    type: Directory
    outputBinding:
      glob: ${ return inputs.output_directory_name }
