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
    def __bool__(self):
        return(bool(self._value))

class BooleanSettingBaseClass(object):
    """
    Similar to SettingBaseClass but accepts a string value and converts it to a boolean
    """
    def __init__(self, value: str) -> None:
        self._value = value
        value = str(value).lower()
        if value == "true":
            value = True
        elif value == "false":
            value = False
        elif value == "none":
            value = False
        else:
            value = bool(value)
        self.value = value

    def __str__(self):
        return(str(self.value))

    def __eq__(self, other):
        return(self.value == other)

    def __bool__(self):
        return(self.value)

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

class UseLSF(BooleanSettingBaseClass):
    """
    better replacement for:

    USE_LSF = os.environ.get('USE_LSF') == "True"

    usage:

    USE_LSF = UseLSF(os.environ.get('USE_LSF', None))
    """
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class EnableLargeTests(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class EnableIntergrationTests(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class KeepTmp(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class PrintCommand(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)
