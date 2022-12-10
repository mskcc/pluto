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
            {
                "value": "toil",
                "toil": True,
                "cwltool": False
            },
            {
                "value": "Toil",
                "toil": True,
                "cwltool": False
            },
            {
                "value": "cwltool",
                "toil": False,
                "cwltool": True
            },
        ]
        for val in values:
            setting = CWLEngine(val['value'])
            self.assertEqual(setting.toil, val['toil'])
            self.assertEqual(setting.cwltool, val['cwltool'])

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
