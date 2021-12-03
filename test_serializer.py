#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for the serializer module
"""
import os
import unittest
import shutil
from serializer import OFile, ODir

if __name__ != "__main__":
    from .tools import PlutoTestCase, CWLFile
if __name__ == "__main__":
    from tools import PlutoTestCase, CWLFile

class TestSerializer(PlutoTestCase):
    def test_cwl_file1(self):
        """
        Test case for serializing an output file object
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
        self.assertCWLDictEqual(obj, expected)

    def test_cwl_file2(self):
        """
        Test case with no 'dir' arg used for OFile; should output just the basename for path
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
        self.assertCWLDictEqual(obj, expected)

    def test_cwl_dir1(self):
        """
        Test case for serializing a directory
        """
        obj = ODir(name = 'portal', dir = '/tmp/foo', items = [])
        expected = {
            'basename': 'portal',
            'class': 'Directory',
            'location': 'file:///tmp/foo/portal',
            'path': '/tmp/foo/portal',
            'listing': []
        }
        self.assertCWLDictEqual(obj, expected)

    def test_cwl_dir2(self):
        """
        Test case for serializing a Directory with a File in it
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
        self.assertCWLDictEqual(_dir, expected)

    def test_cwl_dir3(self):
        """
        Test using temp dir to dynamically generate the output paths
        """
        _file = OFile(size = 488, name = 'Sample4_purity.seg', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
        _dir = ODir(name = 'portal', dir = self.tmpdir, items = [_file])
        expected = {
            'basename': 'portal',
            'class': 'Directory',
            'location': 'file://'+ os.path.join(self.tmpdir, 'portal'),
            'path': os.path.join(self.tmpdir, 'portal'),
            'listing': [
                {
                'basename': 'Sample4_purity.seg',
                'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
                'class': 'File',
                'location': 'file://' + os.path.join(self.tmpdir, 'portal/Sample4_purity.seg'),
                'path': os.path.join(self.tmpdir, 'portal/Sample4_purity.seg'),
                'size': 488
                }
            ]
        }

        self.maxDiff = None
        self.assertCWLDictEqual(_dir, expected)

    def test_assertCWLDictEqual(self):
        """
        Test that the test_assertCWLDictEqual method works with serialized objects
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
        self.maxDiff = None
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



# The next test cases are going to run an actual CWL to test against their results
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
        self.assertCWLDictEqual(output_json, expected_output)


class TestSerializeCWLDirOutput(PlutoTestCase):
    """
    Test cases for using the serializer when output contains directories
    """
    CWL_DIR = os.path.abspath('cwl')
    cwl_file = CWLFile('put_in_dir.cwl', CWL_DIR = CWL_DIR)

    @unittest.skipIf(has_cwl_runner!=True, "need cwl runner for this test")
    def test_put_in_dir1(self):
        """
        Test case for dir output object
        """
        lines = [
            ['# comment 1']
        ]
        input = self.write_table(tmpdir = self.tmpdir, filename = 'input.maf', lines = lines)

        self.input = {
            "item": {"class": "File", "path": input},
            "output_directory_name":  'foo_output',
            }
        output_json, output_dir = self.run_cwl()

        expected_output = {
            'directory': ODir(name = 'foo_output', dir = output_dir, items = [
                OFile(name = 'input.maf', size = 12, hash = 'ce7e0e370d46ae73b6478c062dec9f1a2d6bb37e')
            ])
            }
        self.maxDiff = None
        self.assertCWLDictEqual(output_json, expected_output)


class TestSerializeCWLSubDirOutput(PlutoTestCase):
    """
    Test cases for when the output contains subdirectories
    """
    CWL_DIR = os.path.abspath('cwl')
    cwl_file = CWLFile('create_subdir.cwl', CWL_DIR = CWL_DIR)

    @unittest.skipIf(has_cwl_runner!=True, "need cwl runner for this test")
    def test_put_in_subdir(self):
        """
        Test case for dir output object with nested subdir
        """
        self.input = {}
        output_json, output_dir = self.run_cwl()
        expected_output = {
            # /.../output/foo
            'output_dir': ODir(name = 'foo', dir = output_dir, items = [
                OFile(name = 'input.maf', size = 12, hash = 'ce7e0e370d46ae73b6478c062dec9f1a2d6bb37e')
            ]),
            # /.../output/bar/foo
            'output_subdir': ODir(name = 'bar', dir = output_dir, items = [
                ODir(name = 'foo', items = [
                    OFile( # /.../output/bar/foo/input.maf
                    name = 'input.maf', size = 12, hash = 'ce7e0e370d46ae73b6478c062dec9f1a2d6bb37e')
                ])
            ])
            }
        self.maxDiff = None
        self.assertCWLDictEqual(output_json, expected_output)

if __name__ == "__main__":
    unittest.main()
