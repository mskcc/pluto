#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["touch"]

requirements:
  - class: InlineJavascriptRequirement

inputs:
  input_file:
    type: File
  secondaryFilename:
    type: string
    inputBinding:
      position: 1

outputs:
  output_file:
    type: File
    outputBinding:
      outputEval: |
        ${
          var ret = inputs.input_file;
          ret['secondaryFiles'] = [{"class":"File", "path":runtime.outdir + "/" + inputs.secondaryFilename}];
          return ret;
        }
