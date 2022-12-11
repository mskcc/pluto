#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for the serializer assertCWLDictEqual method
because its one of the most important methods in the test suite,
for validating the output items from a CWL workflow

"""
import os
import unittest
from serializer import OFile, ODir
from tools import (
        PlutoTestCase,
        CWLFile
    )

class TestAssertCWLDictEqual(PlutoTestCase):
    def test_assertCWLDictEqual(self):
        """
        Test that the assertCWLDictEqual method works with serialized objects
        """
        # test single File output
        obj = OFile(size = 488, name = 'Sample4_purity.seg', dir = '/tmp/foo', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
        expected = {
            'basename': 'Sample4_purity.seg',
            'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
            'class': 'File',
            'location': 'file:///tmp/foo/Sample4_purity.seg',
            'path': '/tmp/foo/Sample4_purity.seg',
            'size': 488,
            'nameext' : '.seg',
            'nameroot' : 'Sample4_purity'
        }
        self.assertCWLDictEqual(obj, expected)

        # test nested Dir with File output
        _file = OFile(size = 488, name = 'Sample4_purity.seg', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
        _dir = ODir(name = 'portal', dir = self.tmpdir, items = [_file])
        expected = {
            'basename': 'portal',
            'class': 'Directory',
            'location': 'file://'+ os.path.join(self.tmpdir, 'portal'),
            'path': os.path.join(self.tmpdir, 'portal'),
            'nameext' : '',
            'nameroot' : 'portal',
            'listing': [
                {
                'basename': 'Sample4_purity.seg',
                'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
                'class': 'File',
                'location': 'file://' + os.path.join(self.tmpdir, 'portal/Sample4_purity.seg'),
                'path': os.path.join(self.tmpdir, 'portal/Sample4_purity.seg'),
                'size': 488,
                'nameext' : '.seg',
                'nameroot' : 'Sample4_purity'
                }
            ]
        }
        self.assertCWLDictEqual(_dir, expected)

    def test_assertCWLDictEqual_related1(self):
        """
        Test that values with different "related" key fields don't break the test case
        because they should get removed prior to comparing the dicts
        This is for items like html files, where size and hash can be different on repeated runs
        due to things like embedded timestamps
        """
        # test nested Dir and Files with some items that need extra fields cleaned
        # using the default setting for this case
        _file = OFile(size = 123, name = 'sample.txt', hash = 'samplehash1')
        _report = OFile(size = 456, name = 'report.html', hash = 'foo1')
        _dir = ODir(name = 'output', dir = self.tmpdir, items = [_file, _report])
        expected = {
            'basename': 'output',
            'class': 'Directory',
            'location': 'file://'+ os.path.join(self.tmpdir, 'output'),
            'path': os.path.join(self.tmpdir, 'output'),
            'nameext' : '',
            'nameroot' : 'output',
            'listing': [
                {
                'basename': 'sample.txt',
                'checksum': 'sha1$samplehash1',
                'class': 'File',
                'location': 'file://' + os.path.join(self.tmpdir, 'output/sample.txt'),
                'path': os.path.join(self.tmpdir, 'output/sample.txt'),
                'size': 123,
                'nameext' : '.txt',
                'nameroot' : 'sample'
                },
                {
                'basename': 'report.html',
                'checksum': 'sha1$foo2', # <- this value doesnt match the original but it will get stripped off
                'class': 'File',
                'location': 'file://' + os.path.join(self.tmpdir, 'output/report.html'),
                'path': os.path.join(self.tmpdir, 'output/report.html'),
                'size': 457, # <- this value doesnt match the original but it will get stripped off
                'nameext' : '.html',
                'nameroot' : 'report'
                }
            ]
        }
        self.assertCWLDictEqual(_dir, expected)

        # This time use a custom mapping
        _file = OFile(size = 123, name = 'sample.txt', hash = 'samplehash1')
        _report = OFile(size = 456, name = 'report1.html', hash = 'foo1')
        _dir = ODir(name = 'output', dir = self.tmpdir, items = [_file, _report])
        expected = {
            'basename': 'output',
            'class': 'Directory',
            'location': 'file://'+ os.path.join(self.tmpdir, 'output'),
            'path': os.path.join(self.tmpdir, 'output'),
            'nameext' : '',
            'nameroot' : 'output',
            'listing': [
                {
                'basename': 'sample.txt',
                'checksum': 'sha1$samplehash1',
                'class': 'File',
                'location': 'file://' + os.path.join(self.tmpdir, 'output/sample.txt'),
                'path': os.path.join(self.tmpdir, 'output/sample.txt'),
                'size': 123,
                'nameext' : '.txt',
                'nameroot' : 'sample'
                },
                {
                'basename': 'report1.html',
                'checksum': 'sha1$foo2', # <- this value doesnt match the original but it will get stripped off
                'class': 'File',
                'location': 'file://' + os.path.join(self.tmpdir, 'output/report1.html'),
                'path': os.path.join(self.tmpdir, 'output/report1.html'),
                'size': 457, # <- this value doesnt match the original but it will get stripped off
                'nameext' : '.html',
                'nameroot' : 'report1'
                }
            ]
        }
        related_keys = [
            ('basename', "report1.html", ['size', 'checksum'])
            ]
        self.assertCWLDictEqual(_dir, expected, related_keys = related_keys)


if __name__ == "__main__":
    unittest.main()
