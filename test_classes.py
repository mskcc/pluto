#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import unittest

# TODO: fix these imports somehow
try:
    from .classes import (
        SettingBaseClass,
        BooleanSettingBaseClass,
        CWLEngine
    )
except ImportError:
    from classes import (
        SettingBaseClass,
        BooleanSettingBaseClass,
        CWLEngine
    )

class TestSettingClasses(unittest.TestCase):
    def test_setting(self):
        """
        """
        setting = SettingBaseClass('Foo')
        self.assertEqual(setting, 'foo' )

        setting = SettingBaseClass(None)
        self.assertEqual(setting, "none")

        setting = SettingBaseClass("none")
        self.assertEqual(setting, "none")

    def test_cwl_engine(self):
        """
        """
        setting = CWLEngine("toil")
        self.assertEqual(setting.toil, True)
        self.assertEqual(setting.cwltool, False)

        setting = CWLEngine("Toil")
        self.assertEqual(setting.toil, True)
        self.assertEqual(setting.cwltool, False)

        setting = CWLEngine("cwltool")
        self.assertEqual(setting.toil, False)
        self.assertEqual(setting.cwltool, True)

    def test_bool_setting(self):
        """
        """
        # recognized values that return True
        setting = BooleanSettingBaseClass('True')
        self.assertEqual(setting, True)

        setting = BooleanSettingBaseClass('true')
        self.assertEqual(setting, True)

        setting = BooleanSettingBaseClass('t')
        self.assertEqual(setting, True)

        setting = BooleanSettingBaseClass('T')
        self.assertEqual(setting, True)

        setting = BooleanSettingBaseClass('none')
        self.assertEqual(setting, False)

        # recognized values that return False
        setting = BooleanSettingBaseClass(None)
        self.assertEqual(setting, False)

        setting = BooleanSettingBaseClass("False")
        self.assertEqual(setting, False)

        setting = BooleanSettingBaseClass("false")
        self.assertEqual(setting, False)

        setting = BooleanSettingBaseClass("f")
        self.assertEqual(setting, False)

        setting = BooleanSettingBaseClass("F")
        self.assertEqual(setting, False)

        setting = BooleanSettingBaseClass("0")
        self.assertEqual(setting, False)

        setting = BooleanSettingBaseClass("")
        self.assertEqual(setting, False)

        # any other string values return True
        setting = BooleanSettingBaseClass(" ")
        self.assertEqual(setting, True)

        setting = BooleanSettingBaseClass("foo")
        self.assertEqual(setting, True)

        setting = BooleanSettingBaseClass("1")
        self.assertEqual(setting, True)


if __name__ == "__main__":
    unittest.main()
