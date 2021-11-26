#!/usr/bin/env cwl-runner

cwlVersion: v1.0

class: CommandLineTool
baseCommand: [ "sh", "run.sh" ]
requirements:
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entryname: run.sh
        entry: |-
          input_file="input.maf"
          echo "# comment 1" > "\${input_file}"
          # /.../output/foo/input.maf
          output_dir_name="foo"
          mkdir "\${output_dir_name}"
          cp "\${input_file}" "\${output_dir_name}/input.maf"
          # /.../output/bar/foo/input.maf
          output_subdir_name="bar"
          output_subdir_path="\${output_subdir_name}/\${output_dir_name}"
          mkdir -p "\${output_subdir_path}"
          cp "\${input_file}" "\${output_subdir_path}/input.maf"

inputs: []

outputs:
  # /.../output/foo/input.maf
  output_dir:
    type: Directory
    outputBinding:
      glob: ${ return "foo" }
  # /.../output/bar/foo/input.maf
  output_subdir:
    type: Directory
    outputBinding:
      glob: ${ return "bar" }
