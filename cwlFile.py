import os
from .settings import CWL_DIR as _CWL_DIR

class CWLFile(os.PathLike):
    """
    Wrapper class to locate the full path to a cwl file more conveniently
    """
    def __init__(self, path: str, CWL_DIR: str = None):
        """
        Parameters
        ----------
        path: str
            name of a CWL file relative to `CWL_DIR`
        CWL_DIR: str
            full path to the directory containing CWL files


        Examples
        --------
        Example usage::

            cwl_file = CWLFile("foo.cwl")
        """
        if CWL_DIR is None:
            CWL_DIR = _CWL_DIR
        self.path = os.path.join(CWL_DIR, path)
    def __str__(self):
        return(self.path)
    def __repr__(self):
        return(self.path)
    def __fspath__(self):
        return(self.path)
