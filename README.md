# pluto

[![Documentation Status](https://readthedocs.org/projects/pluto-util/badge/?version=latest)](https://pluto-util.readthedocs.io/en/latest/?badge=latest)

**P**ost-processing & **L**ightweight **U**pdates **T**o pipeline **O**utput

Utilities module for [pluto-cwl](https://github.com/mskcc/pluto-cwl) and [helix_filters_01](https://github.com/mskcc/helix_filters_01) repos

This repository contains object classes to make it easier to run CWL files, and to run test cases against CWL files. 

Repo contents include:

#### Python Libraries

`tools.py`

- `CWLFile`: convenience class to map a CWL file by basename back to its full object path in relation to the `cwl` dir
- `CWLRunner`: helper class for running a CWL file from the command line via `cwltool` or Toil
- `TableReader`, `MafReader`: class for reading data from tabular files
- `MafWriter`: class for writing records to a tabular .maf format file
- `PlutoTestCase`: the most important class in the `pluto` module, this class bundles a large variety of helper methods and functionality into a standard Python `unittest.TestCase` object to reduce the amount of code needed when writing CWL test cases, and to provide an easy standard interface to control CWL test case execution parameters. Uses environment variables inherited from `settings.py` to control how tests are executed. Also includes a large number of custom test case 'assertion' methods in order to easily validate CWL workflow outputs. A noteworthy method is `assertCWLDictEqual` which performs a `cwltool`/Toil-agnostic comparison of CWL JSON dict's to validate workflow output.


`settings.py`

- contains a large amount of environment variables that can be supplied on the command line to control how CWL and test cases are executed

`serializer.py`

- `OFile`, `ODir`: special subclasses of the base Python `dict` object which are used to simulate the standard CWL JSON dict record format of workflow output item descriptions. Use these classes to create objects that expand out to a full CWL JSON, in order to use with methods such as `assertDictEquals`. The class signature is designed for succint expression of a large dynamically generated dictionary structure, and can cleanly reduce a standard CWL JSON representation in-code from ~8 lines down to 1-2 lines. 
- `serializer.py` can also be run as a script on the saved output.json from a CWL workflow in order to convert a workflow output JSON into its Python representation using `OFile` and `ODir`, to allow for quickly creating new fixtures from existing JSON outputs.

#### Scripts

- `Makefile`: contains the install recipe for the `pluto` repo, and testing recipe for `pluto` itself
- `run-cwltool.sh`: convenience wrapper script for running a CWL with `cwltool`
- `run-toil.sh`: convenience wrapper script for running a CWL with Toil (this is the one you probably should be using)
- `env.juno.sh`: environment initialization script for use on MSKCC's Juno HPC cluster
- `scripts/`: more handy scripts for tedious tasks

