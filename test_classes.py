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
        values = [
            ('Foo', 'foo'),
            (None, "none"),
            ("none", "none")
        ]
        for val, expected in values:
            self.assertEqual(SettingBaseClass(val), expected)

    def test_cwl_engine(self):
        """
        """
        values = [
            # only settings explicitly labeled as "toil" should enable Toil, 
            # all others should default to cwltool
            { "value": "toil", "toil": True, "cwltool": False, "equiv_cwltool": False },
            { "value": "Toil", "toil": True, "cwltool": False, "equiv_cwltool": False },
            { "value": "cwltool", "toil": False, "cwltool": True, "equiv_cwltool": True },
            { "value": "none", "toil": False, "cwltool": True, "equiv_cwltool": True },
            { "value": "None", "toil": False, "cwltool": True, "equiv_cwltool": True },
            { "value": None, "toil": False, "cwltool": True, "equiv_cwltool": True },
            { "value": True, "toil": False, "cwltool": True, "equiv_cwltool": True },
            { "value": False, "toil": False, "cwltool": True, "equiv_cwltool": True },
            { "value": "fooooo", "toil": False, "cwltool": True, "equiv_cwltool": True },
        ]
        for val in values:
            setting = CWLEngine(val['value'])
            got = (setting.toil, setting.cwltool, setting == "cwltool")
            want = (val['toil'], val['cwltool'], val['equiv_cwltool'])
            message = "ERROR with {}, got: {}, want: {}".format(
                setting.__repr__(),
                got,
                want
            )
            self.assertEqual(got, want, message)

    def test_bool_setting(self):
        """
        """
        values = [
            # recognized values that return True
            ('True', True),
            ('true', True),
            ('t', True),
            ('T', True),
            # recognized values that return False
            (None, False),
            ("None", False),
            ('none', False),
            (False, False),
            ("False", False),
            ("false", False),
            ("f", False),
            ("F", False),
            ("0", False),
            ("", False),
            # any other string values return True
            (" ", True),
            ("foo", True),
            ("1", True)
        ]
        for value, expected in values:
            self.assertEqual(BooleanSettingBaseClass(value), expected)


if __name__ == "__main__":
    unittest.main()
