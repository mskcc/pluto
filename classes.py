"""
Helper classes to use throughout the pluto module
TODO: move more classes into this module
"""

class SettingBaseClass(object):
    """
    Base class for Setting's, will accept a string value, clean it up, and store it
    Allows for comparisons to be made with '=='

    setting = SettingBaseClass('Foo')
    setting == 'foo' # True
    """
    def __init__(self, value: str = None, default: str = None) -> None:
        self._value = value # the original value in case we need it again
        self._default = default
        if value is None:
            value = default
        value = str(value).lower()
        self.value = value

    def __str__(self):
        return(self.value)
    def __eq__(self, other):
        return(self.value == other)

class CWLEngine(SettingBaseClass):
    """
    CWL_ENGINE = CWLEngine(os.environ.get('CWL_ENGINE', None))
    if CWL_ENGINE:
        do_foo()
    if CWL_ENGINE.toil:
        do_toil()
    """
    def __init__(self, value: str = None, default: str = 'cwltool', *args, **kwargs):
        super().__init__(value, default, *args, **kwargs)
        self.cwltool = self.value == "cwltool"
        self.toil = self.value == "toil"
