"""
Helper classes to use throughout the pluto module
TODO: move more classes into this module
"""
from typing import Optional, Union

class NeedsOverrideError(Exception):
    """
    Exception to throw when some class method or attribute should have been overriden in a subclass 
    but wasnt and so a placeholder default got executed
    """
    pass

class MissingCWLError(NeedsOverrideError):
    """
    Exception object type to use as placeholder when some other CWL object or path should have been used
    """
    pass

class MissingResultObjError(NeedsOverrideError):
    pass

class MissingTestCaseError(NeedsOverrideError):
    pass

class SettingBaseClass(object):
    """
    Base class for Setting's, will accept a string value, clean it up, and store it
    Allows for comparisons to be made with '=='

    setting = SettingBaseClass('Foo')
    setting == 'foo' # True
    """
    def __init__(self, value: Optional[str] = None, default: Optional[str] = None) -> None:
        self._value = value # the original value in case we need it again
        self._default = default
        if value is None:
            value = default
        value = str(value).lower()
        self.value = value

    def __str__(self):
        return(self.value)
    def __repr__(self):
        return("SettingBaseClass(" + self._value.__repr__() + ")")
    def __eq__(self, other):
        return(self.value == other)
    def __bool__(self):
        return(bool(self._value))

class CWLEngine(SettingBaseClass):
    """
    CWL_ENGINE = CWLEngine(os.environ.get('CWL_ENGINE', None))
    if CWL_ENGINE:
        do_foo()
    if CWL_ENGINE.toil:
        do_toil()
    if CWL_ENGINE == 'cwltool':
        do_someting()
    """
    def __init__(self, value: str = None, default: str = 'cwltool', *args, **kwargs):
        super().__init__(value, default, *args, **kwargs)
        self.cwltool = self.value == "cwltool"
        self.toil = self.value == "toil"

        # re-apply the defaults if neither was correctly set
        if not self.cwltool and not self.toil:
            self.cwltool = True
        # if an invalid value was passed, default to cwltool
        if self.value not in {"cwltool", "toil"}:
            self.cwltool = True
        
        # store a string for the name for comparisons, default to cwltool
        self.engine_name = "cwltool"
        if self.toil:
            self.engine_name = "toil"
    
    def __eq__(self, other):
        return(self.engine_name == other)


class BooleanSettingBaseClass(object):
    """
    Similar to SettingBaseClass but accepts a string value and converts it to a boolean
    Recognizes some specific string values for direct true/false mappings, otherwise passes down to `bool()`
    """
    def __init__(self, value: Union[str, bool]) -> None:
        self._value = value # save the original value passed in
        self.value = self.parse(value) # get the parsed value converted to boolean

    def parse(self, value: Union[str, bool]) -> bool:
        """
        Recognize a few specific strings to return pre-definied values for, otherwise use `bool()`
        """
        result = False # default value
        value = str(value).lower()
        if value == "true":
            result = True
        elif value == "false":
            result = False
        elif value == "f":
            result = False
        elif value == "none":
            result = False
        elif value == "0":
            result = False
        else:
            result = bool(value) # any other non-empty string values will be True here
        return(result)

    def __str__(self):
        return(str(self.value))
    
    def __repr__(self):
        return("BooleanSettingBaseClass(" + self._value.__repr__() + ")" )

    def __eq__(self, other):
        return(self.value == other)

    def __bool__(self):
        return(self.value)


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

class PrintTestName(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class SuppressStartupMessages(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class ToilStats(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class PrintToilStats(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)

class SaveToilStats(BooleanSettingBaseClass):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(value, *args, **kwargs)
