#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for the serializer module
"""
import os
import unittest
import shutil
import json
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


class TestRepr(PlutoTestCase):
    def test_repr_ofile(self):
        """
        Test that we can output a representation of the object that can be used
        to recreate the object
        """
        # create OFile object with classmethod; this saves the args
        f = OFile.init(name = 'input.maf', size = 12, hash = '12345')
        # create a string representation of the object
        r = f.repr()
        # its expected to look like this:
        e = """OFile(name='input.maf', size=12, hash='12345')"""
        self.assertEqual(r, e)
        # use the string repr to create a new copy of the obj
        x = eval(r)
        # test that the old and new obj's are equivalent
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(f, attr), getattr(x, attr))
        self.assertEqual(f.items(), x.items())

        f = OFile.init('input.maf', size = 12, hash = '12345')
        r = f.repr()
        e = """OFile('input.maf', size=12, hash='12345')"""
        self.assertEqual(r, e)
        x = eval(r)
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(f, attr), getattr(x, attr))
        self.assertEqual(f.items(), x.items())

        f = OFile.init('input.maf', size = 12, class_label = 'foo')
        r = f.repr()
        e = """OFile('input.maf', size=12, class_label='foo')"""
        self.assertEqual(r, e)
        x = eval(r)
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(f, attr), getattr(x, attr))
        self.assertEqual(f.items(), x.items())

        f = OFile.init('input.maf', None, 12)
        r = f.repr()
        e = """OFile('input.maf', None, 12)"""
        self.assertEqual(r, e)
        x = eval(r)
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(f, attr), getattr(x, attr))
        self.assertEqual(f.items(), x.items())

    def test_repr_odir(self):
        """
        Test that we can output a representation of the object that can be used
        to recreate the object
        """
        # create ODir object with classmethod; this saves the args
        d = ODir.init(name = 'output', items = [])
        # create a string representation of the object
        r = d.repr()
        # its expected to look like this:
        e = """ODir(name='output', items=[])"""
        self.assertEqual(r, e)
        # use the string repr to create a new copy of the obj
        x = eval(r)
        # test that the old and new obj's are equivalent
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(d, attr), getattr(x, attr))
        self.assertEqual(d.items(), x.items())


        d = ODir.init('output', items = [])
        r = d.repr()
        e = """ODir('output', items=[])"""
        self.assertEqual(r, e)
        x = eval(r)
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(d, attr), getattr(x, attr))
        self.assertEqual(d.items(), x.items())


        d = ODir.init(name = 'foo', dir = '/output', items = [
                OFile.init(name = 'input.maf', size = 12, hash ='1234')])
        r = d.repr()
        e = """ODir(name='foo', dir='/output', items=[OFile(name='input.maf', size=12, hash='1234')])"""
        self.maxDiff = None
        self.assertEqual(r, e)
        x = eval(r)
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(d, attr), getattr(x, attr))
        self.assertEqual(d.items(), x.items())


        d = ODir.init(name = 'bar', dir = '/output', items = [
            ODir.init(name = 'foo', items = [
                OFile.init( # /.../output/bar/foo/input.maf
                name = 'input.maf', size = 12, hash = '1234')
            ])
        ])
        r = d.repr()
        e = """ODir(name='bar', dir='/output', items=[ODir(name='foo', items=[OFile(name='input.maf', size=12, hash='1234')])])"""
        self.assertEqual(r, e)
        x = eval(r)
        for attr in [ 'path', 'location' ]:
            self.assertEqual(getattr(d, attr), getattr(x, attr))
        self.assertEqual(d.items(), x.items())

class TestLoadJSON(PlutoTestCase):
    def test_load_ofile_from_repr(self):
        """
        Initialize OFile objects from a JSON blob
        """
        json_str = """{
                        "location": "file:///output/Sample1.maf",
                        "basename": "Sample1.maf",
                        "nameroot": "Sample1",
                        "nameext": ".maf",
                        "class": "File",
                        "checksum": "sha1$12345",
                        "size": 108887494
                    }"""
        data = json.loads(json_str)
        f = OFile.init_dict(data)
        ex = {'basename': 'Sample1.maf', 'class': 'File', 'size': 108887494, 'checksum': 'sha1$12345', 'location': 'file:///output/Sample1.maf', 'path': '/output/Sample1.maf'}
        self.assertCWLDictEqual(f, ex)
        r = f.repr()
        ex2 = """OFile(name='Sample1.maf', size=108887494, hash='12345', dir='/output')"""
        self.assertEqual(r, ex2)
        f2 = eval(r)
        self.assertCWLDictEqual(f2, ex)

        f = OFile.init_dict(data, in_subdir = True)
        ex = {'basename': 'Sample1.maf', 'class': 'File', 'size': 108887494, 'checksum': 'sha1$12345',
            'location': 'file://Sample1.maf', 'path': 'Sample1.maf'} # NOTE: location and path here are wrong but this is meant to be overriden by the parent ODir object... should not show up in repr()
        self.assertCWLDictEqual(f, ex)
        r = f.repr()
        ex = """OFile(name='Sample1.maf', size=108887494, hash='12345')"""
        self.assertEqual(r, ex)

    def test_load_odir_from_repr(self):
        """
        Initialize ODir objects from JSON blob
        """
        json_str = """{
            "class": "Directory",
            "basename": "analysis",
            "listing": [
                {
                    "location": "file:///output/analysis/cna.txt",
                    "basename": "cna.txt",
                    "nameroot": "cna",
                    "nameext": ".txt",
                    "class": "File",
                    "checksum": "sha1$1234",
                    "size": 6547460
                }
            ],
            "location": "file:///output/analysis"
        }"""
        data = json.loads(json_str)
        d = ODir.init_dict(data)
        ex = {'basename': 'analysis', 'class': 'Directory', 'location': 'file:///output/analysis', 'path': '/output/analysis', 'listing': [
            {'basename': 'cna.txt', 'class': 'File', 'size': 6547460, 'checksum': 'sha1$1234', 'location': 'file:///output/analysis/cna.txt', 'path': '/output/analysis/cna.txt'}
        ]}
        self.assertCWLDictEqual(d, ex)
        r = d.repr()
        ex2 = """ODir(name='analysis', items=[OFile(name='cna.txt', size=6547460, hash='1234')], dir='/output')"""
        self.assertEqual(r, ex2)
        d2 = eval(r)
        self.assertCWLDictEqual(d2, ex)
        # self.assertCWLDictEqual(d2, data)



        json_str = """{
            "class": "Directory",
            "basename": "portal",
            "listing": [
                {
                    "location": "file:///output/portal/meta_clinical_sample.txt",
                    "basename": "meta_clinical_sample.txt",
                    "nameroot": "meta_clinical_sample",
                    "nameext": ".txt",
                    "class": "File",
                    "checksum": "sha1$1234",
                    "size": 135
                },
                {
                    "class": "Directory",
                    "basename": "case_lists",
                    "listing": [
                        {
                            "location": "file:///output/portal/case_lists/cases_all.txt",
                            "basename": "cases_all.txt",
                            "nameroot": "cases_all",
                            "nameext": ".txt",
                            "class": "File",
                            "checksum": "sha1$4567",
                            "size": 448
                        }
                    ],
                    "location": "file:///output/portal/case_lists"
                },
                {
                    "location": "file:///output/portal/report.html",
                    "basename": "report.html",
                    "nameroot": "report",
                    "nameext": ".html",
                    "class": "File",
                    "checksum": "sha1$7890",
                    "size": 1026290
                }
            ],
            "location": "file:///output/portal"
        }"""
        data = json.loads(json_str)
        d = ODir.init_dict(data)
        ex = {'basename': 'portal', 'class': 'Directory', 'location': 'file:///output/portal', 'path': '/output/portal', 'listing': [
            {'basename': 'meta_clinical_sample.txt', 'class': 'File', 'size': 135, 'checksum': 'sha1$1234', 'location': 'file:///output/portal/meta_clinical_sample.txt', 'path': '/output/portal/meta_clinical_sample.txt'},
            {'basename': 'case_lists', 'class': 'Directory', 'location': 'file:///output/portal/case_lists', 'path': '/output/portal/case_lists', 'listing': [
                {'basename': 'cases_all.txt', 'class': 'File', 'size': 448, 'checksum': 'sha1$4567', 'location': 'file:///output/portal/case_lists/cases_all.txt', 'path': '/output/portal/case_lists/cases_all.txt'}
            ]},
            {'basename': 'report.html', 'class': 'File', 'size': 1026290, 'checksum': 'sha1$7890', 'location': 'file:///output/portal/report.html', 'path': '/output/portal/report.html'}
            ]}
        self.assertCWLDictEqual(d, ex)
        r = d.repr()
        ex2 = """ODir(name='portal', items=[OFile(name='meta_clinical_sample.txt', size=135, hash='1234'), ODir(name='case_lists', items=[OFile(name='cases_all.txt', size=448, hash='4567')]), OFile(name='report.html', size=1026290, hash='7890')], dir='/output')"""
        self.assertEqual(r, ex2)
        d2 = eval(r)
        self.assertCWLDictEqual(d2, ex)


if __name__ == "__main__":
    unittest.main()
