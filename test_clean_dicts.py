#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test cases for tools.clean_dicts, which is the core scrubbing logic behind assertCWLDictEqual, 
which makes up the most important CWL validation methods in the pluto module
"""
import os
import unittest
from tools import (
        PlutoTestCase, 
        clean_dicts
    )

class TestCleanDicts(PlutoTestCase):
    def test_clean_keys_from_dict(self):
        """
        Test case for scrubbing certain keys from a single dict
        """
        # simple case of dict with no nesting
        d = {'a':1}
        expected = {'a':1}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        d = {'a':1, 'nameext': "foo"}
        expected = {'a':1}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        d = {'a':1, 'nameext': "foo", 'nameroot':'bar'}
        expected = {'a':1}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        d = {'a':1, 'nameroot':'bar'}
        expected = {'a':1}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        # dict that has nested dict of dict values
        d = {'a':1, 'b':{'c':1}}
        expected = {'a':1, 'b':{'c':1}}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        d = {'a':1, 'b':{'c':1, 'nameext': "foo", 'nameroot':'bar'}}
        expected = {'a':1, 'b':{'c':1}}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        # dict that has nested list of dict values
        d = {'a':1, 'b':[{'c':1}]}
        expected = {'a':1, 'b':[{'c':1}]}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        d = {'a':1, 'b':[{'c':1, 'nameext': "foo"}]}
        expected = {'a':1, 'b':[{'c':1}]}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        d = {'a':1, 'b':[{'c':1, 'nameroot': "foo"}]}
        expected = {'a':1, 'b':[{'c':1}]}
        clean_dicts(d)
        self.assertDictEqual(d, expected)

        # list of dicts with nested values
        l = [{'a':1, 'nameroot':'bar'}, {'a':1, 'nameext':'foo'}]
        expected = [{'a':1}, {'a':1}]
        clean_dicts(l)
        self.assertEqual(l, expected)

        l = [123, {'a':1, 'nameroot':'bar'}, {'a':1, 'c':[{'d':1, 'nameroot':'bar'}]}]
        expected = [123, {'a':1}, {'a':1, 'c':[{'d':1}]}]
        clean_dicts(l)
        self.assertEqual(l, expected)

    def test_clean_related_keys_from_dict1(self):
        """
        Remove some dict keys if a given key matches a given value
        This mimics known CWL output formats
        where we need to remove 'size' and 'checksum' on files such as .html
        because they often contain things like embedded timestamps, etc., that make it
        difficult to test against because sizes and checksums fluctute with repeated generation
        """
        d = {'basename': "report.html", "class": "File", 'size': "1", "checksum": "foobar"}
        related_keys = [('basename', "report.html", ['size', 'checksum'])]
        expected = {'basename': "report.html", "class": "File"}
        clean_dicts(d, related_keys = related_keys)
        self.assertDictEqual(d, expected)

    def test_clean_related_keys_from_dict2(self):
        """
        The same as test_clean_related_keys_from_dict1 but this time with a more complicated
        real-life format of CWL output with nested dir listings
        """
        d = {
        "output_dir": {
            "class": "Directory",
            "location": "/foo/bar/output",
            "basename": "output",
            "listing":[
                {"class": "File", "basename": "report.html", "size": "1", "checksum": "foobarhash"},
                {"class": "File", "basename": "samples.txt", "size": "2", "checksum": "foobarhash2"},
                {"class": "Directory", "basename": "more_reports", "location": "/foo/bar/output/more_reports", "listing":[
                    {"class": "File", "basename": "igv_report1.html", "size": "3", "checksum": "foobarhash3"}
                ]}
                ]
            },
        "mutations_file": {
            "class": "File", "basename": "mutations.txt", "size": "4", "checksum": "foobarhash4", 'nameext': ".txt", 'nameroot':'mutations'
            }
        }
        expected = {
        "output_dir": {
            "class": "Directory",
            "location": "/foo/bar/output",
            "basename": "output",
            "listing":[
                {"class": "File", "basename": "report.html"}, # , "size": "1", "checksum": "foobarhash"
                {"class": "File", "basename": "samples.txt", "size": "2", "checksum": "foobarhash2"},
                {"class": "Directory", "basename": "more_reports", "location": "/foo/bar/output/more_reports", "listing":[
                    {"class": "File", "basename": "igv_report1.html"} # , "size": "3", "checksum": "foobarhash3"
                ]}
                ]
            },
        "mutations_file": {"class": "File", "basename": "mutations.txt", "size": "4", "checksum": "foobarhash4"} # , 'nameext': ".txt", 'nameroot':'mutations'
        }
        related_keys = [
            ('basename', "report.html", ['size', 'checksum']),
            ('basename', "igv_report1.html", ['size', 'checksum'])
            ]
        clean_dicts(d, related_keys = related_keys)
        self.maxDiff = None
        self.assertDictEqual(d, expected)

if __name__ == "__main__":
    unittest.main()
