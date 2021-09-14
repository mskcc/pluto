#!/usr/bin/env cwl-runner

# workflow for putting a File into a Directory, then putting that Directory into a subdir

cwlVersion: v1.0
class: Workflow

requirements:
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}
  SubworkflowFeatureRequirement: {}

inputs:
  output_dir_name: string
  output_subdir_name: string
  item: File

steps:
  put_in_dir:
    run: put_in_dir.cwl
    in:
      item: item
      output_directory_name: output_dir_name
    out:
      [ directory ]

  put_in_subdir:
    run: put_in_dir.cwl
    in:
      item: put_in_dir/directory
      output_directory_name: output_subdir_name
    out:
      [ directory ]

outputs:
  output_dir:
    type: Directory
    outputSource: put_in_dir/directory
  output_subdir:
    type: Directory
    outputSource: put_in_subdir/directory
