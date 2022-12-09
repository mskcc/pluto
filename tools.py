"""
Helper functions for running tests

TODO: deprecate this file and replace it with some other package organization method
this should probably be the __all__.py or __init__.py file
"""
# TODO: fix these imports somehow
try:
    from .settings import (
        CWL_ARGS,
        TOIL_ARGS,
        DATA_SETS,
        KNOWN_FUSIONS_FILE,
        IMPACT_FILE,
        USE_LSF,
        TMP_DIR,
        KEEP_TMP,
        CWL_ENGINE,
        PRINT_COMMAND,
        PRINT_TESTNAME,
        TOIL_STATS,
        PRINT_STATS,
        SAVE_STATS,
        STATS_DIR
    )
    from .settings import CWL_DIR as _CWL_DIR
    from .plutoTestCase import PlutoTestCase
    from .cwlFile import CWLFile
    from .cwlRunner import CWLRunner
    from .util import (
        dicts2lines,
        write_table,
        clean_dicts,
        load_mutations,
        parse_header_comments,
        md5_file, 
        md5_obj
    )
    from .mafio import (
        TableReader,
        MafWriter
    )
except ImportError:
    from settings import (
        CWL_ARGS,
        TOIL_ARGS,
        DATA_SETS,
        KNOWN_FUSIONS_FILE,
        IMPACT_FILE,
        USE_LSF,
        TMP_DIR,
        KEEP_TMP,
        CWL_ENGINE,
        PRINT_COMMAND,
        PRINT_TESTNAME,
        TOIL_STATS,
        PRINT_STATS,
        SAVE_STATS,
        STATS_DIR
    )
    from settings import CWL_DIR as _CWL_DIR
    from plutoTestCase import PlutoTestCase
    from cwlFile import CWLFile
    from cwlRunner import CWLRunner
    from util import (
        dicts2lines,
        write_table,
        clean_dicts,
        load_mutations,
        parse_header_comments,
        md5_file, 
        md5_obj
    )
    from mafio import (
        TableReader,
        MafWriter
    )
