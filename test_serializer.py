#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for the tools module
"""
import os
import unittest
import shutil
from tempfile import TemporaryDirectory
from serializer import OFile, ODir

if __name__ != "__main__":
    from .tools import PlutoTestCase, CWLFile
if __name__ == "__main__":
    from tools import PlutoTestCase, CWLFile

class TestSerializer(unittest.TestCase):
    def test_cwl_file1(self):
        """
        """
        obj = OFile(size = 488, name = 'Sample4_purity.seg', dir = '/tmp/foo', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
        expected = {
            'basename': 'Sample4_purity.seg',
            'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
            'class': 'File',
            'location': 'file:///tmp/foo/Sample4_purity.seg',
            'path': '/tmp/foo/Sample4_purity.seg',
            'size': 488
        }
        self.assertDictEqual(obj, expected)
        self.assertEqual(obj, expected)

    def test_cwl_file2(self):
        """
        Test case with no dir listed
        """
        obj = OFile(size = 488, name = 'Sample4_purity.seg', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
        expected = {
            'basename': 'Sample4_purity.seg',
            'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
            'class': 'File',
            'location': 'file://Sample4_purity.seg',
            'path': 'Sample4_purity.seg',
            'size': 488
        }
        self.assertDictEqual(obj, expected)
        self.assertEqual(obj, expected)

    def test_cwl_dir1(self):
        """
        """
        obj = ODir(name = 'portal', dir = '/tmp/foo', items = [])
        expected = {
            'basename': 'portal',
            'class': 'Directory',
            'location': 'file:///tmp/foo/portal',
            'path': '/tmp/foo/portal',
            'listing': []
        }
        self.assertDictEqual(obj, expected)
        self.assertEqual(obj, expected)


    def test_cwl_dir2(self):
        """
        """
        _file = OFile(size = 488, name = 'Sample4_purity.seg', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
        _dir = ODir(name = 'portal', dir = '/tmp/foo', items = [_file])

        expected = {
            'basename': 'portal',
            'class': 'Directory',
            'location': 'file:///tmp/foo/portal',
            'path': '/tmp/foo/portal',
            'listing': [
                {
                'basename': 'Sample4_purity.seg',
                'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
                'class': 'File',
                'location': 'file:///tmp/foo/portal/Sample4_purity.seg',
                'path': '/tmp/foo/portal/Sample4_purity.seg',
                'size': 488
                }
            ]
        }
        self.maxDiff = None
        self.assertDictEqual(_dir, expected)
        self.assertEqual(_dir, expected)

    def test_cwl_dir3(self):
        """
        Test using temp dir
        """
        with TemporaryDirectory() as tmpdir:
            _file = OFile(size = 488, name = 'Sample4_purity.seg', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
            _dir = ODir(name = 'portal', dir = tmpdir, items = [_file])
            expected = {
                'basename': 'portal',
                'class': 'Directory',
                'location': 'file://'+ os.path.join(tmpdir, 'portal'),
                'path': os.path.join(tmpdir, 'portal'),
                'listing': [
                    {
                    'basename': 'Sample4_purity.seg',
                    'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
                    'class': 'File',
                    'location': 'file://' + os.path.join(tmpdir, 'portal/Sample4_purity.seg'),
                    'path': os.path.join(tmpdir, 'portal/Sample4_purity.seg'),
                    'size': 488
                    }
                ]
            }
            self.maxDiff = None
            self.assertDictEqual(_dir, expected)
            self.assertEqual(_dir, expected)




has_cwl_runner = True if shutil.which('cwl-runner') else False
if not has_cwl_runner:
    print(">>> skipping tests that require cwl-runner")

class TestSerializeCWLOutput(PlutoTestCase):
    CWL_DIR = os.path.abspath('cwl')
    cwl_file = CWLFile('copy.cwl', CWL_DIR = CWL_DIR)

    @unittest.skipIf(has_cwl_runner!=True, "need cwl runner for this test")
    def test_copy1(self):
        """
        Test case for using serialized objects in a CWL test case
        """
        lines = [
            ['# comment 1']
        ]
        input = self.write_table(tmpdir = self.tmpdir, filename = 'input.maf', lines = lines)

        self.input = {
            "input_file": {
                  "class": "File",
                  "path": input
                },
            "output_filename":  'output.maf',
            }
        output_json, output_dir = self.run_cwl()

        expected_output = {
            'output_file': OFile(size = 12, name = 'output.maf', dir = output_dir, hash = 'ce7e0e370d46ae73b6478c062dec9f1a2d6bb37e')
            }
        self.assertDictEqual(output_json, expected_output)


if __name__ == "__main__":
    unittest.main()
