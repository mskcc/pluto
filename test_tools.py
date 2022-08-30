#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for the tools module
"""
import os
import unittest
from tempfile import TemporaryDirectory
import shutil

# relative imports, from CLI and from parent project
if __name__ != "__main__":
    from .tools import md5_file, md5_obj, PlutoTestCase, CWLFile, TableReader, write_table, load_mutations, dicts2lines, MafWriter, clean_dicts
    from .settings import CWL_ENGINE

if __name__ == "__main__":
    from tools import md5_file, md5_obj, PlutoTestCase, CWLFile, TableReader, write_table, load_mutations, dicts2lines, MafWriter, clean_dicts
    from settings import CWL_ENGINE

class TestMd5(unittest.TestCase):
    def test_md5_file(self):
        """
        Test case for getting the md5 of a file
        """
        with TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "file.txt")
            lines = ['foo', 'bar']
            with open(filename, "w") as fout:
                for line in lines:
                    fout.write(line + '\n')
            hash = md5_file(filename)
            self.assertEqual(hash, 'f47c75614087a8dd938ba4acff252494')

    def test_md5_obj(self):
        """
        Test case for getting the md5 of a Python object
        """
        obj = [
            {'a': 1, 'b': "foo"},
            {'bar': 1.0, 'baz': "buzz"},
        ]
        hash = md5_obj(obj)
        expected_hash = 'fc7c5bd4a1aa9114edb7a2a74175b9e9'
        self.assertEqual(hash, expected_hash)




has_cwl_runner = True if shutil.which('cwl-runner') else False
if not has_cwl_runner:
    print(">>> skipping tests that require cwl-runner")

class TestCopyCWL(PlutoTestCase):
    CWL_DIR = os.path.abspath('cwl')
    cwl_file = CWLFile('copy.cwl', CWL_DIR = CWL_DIR)

    @unittest.skipIf(has_cwl_runner!=True, "need cwl runner for this test")
    def test_copy1(self):
        """
        Test case for running the demo copy cwl to copy a file
        """
        lines = [
            ['# comment 1'],
            ['# comment 2'],
            ['Hugo_Symbol', 't_depth', 't_alt_count'],
            ['SUFU', '100', '75'],
            ['GOT1', '100', '1'],
            ['SOX9', '100', '0'],
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
            'output_file': {
                'location': 'file://' + os.path.join(output_dir, 'output.maf'),
                'basename': 'output.maf',
                'class': 'File',
                'checksum': 'sha1$7bcfa105aa117881f032765595bec2e9a016a1e7',
                'size': 90,
                'path': os.path.join(output_dir, 'output.maf')
                }
            }
        expected_path = os.path.join(output_dir, 'output.maf')
        self.assertCWLDictEqual(output_json, expected_output)

        comments, mutations = self.load_mutations(expected_path)

        expected_comments = ['# comment 1', '# comment 2']
        self.assertEqual(comments, expected_comments)

        expected_mutations = [
            {'Hugo_Symbol': 'SUFU', 't_depth': '100', 't_alt_count':'75'},
            {'Hugo_Symbol': 'GOT1', 't_depth': '100', 't_alt_count':'1'},
            {'Hugo_Symbol': 'SOX9', 't_depth': '100', 't_alt_count':'0'}
            ]
        self.assertEqual(mutations, expected_mutations)

    @unittest.skipIf(has_cwl_runner!=True, "need cwl runner for this test")
    def test_copy2(self):
        comments = [
        ['# comment 1'],
        ['# comment 2']
        ]
        maf_row1 = {
            "Hugo_Symbol" : "FGF3",
            "Entrez_Gene_Id" : "2248",
            "Chromosome" : "11",
            "Start_Position" : "69625447",
            "End_Position": "69625448",
            "Tumor_Sample_Barcode": "Sample1-T",
            "Matched_Norm_Sample_Barcode": "Sample1-N",
            }
        maf_row2 = {
            "Hugo_Symbol" : "PNISR",
            "Entrez_Gene_Id" : "25957",
            "Chromosome" : "6",
            "Start_Position" : "99865784",
            "End_Position": "99865785",
            "Tumor_Sample_Barcode": "Sample1-T",
            "Matched_Norm_Sample_Barcode": "Sample1-N",
            }
        maf_rows = [ maf_row1, maf_row2 ]
        maf_lines = self.dicts2lines(dict_list = maf_rows, comment_list = comments)
        input_maf = self.write_table(tmpdir = self.tmpdir, filename = 'input.maf', lines = maf_lines)

        self.input = {
            "input_file": {
                  "class": "File",
                  "path": input_maf
                },
            "output_filename":  'output.maf',
            }
        output_json, output_dir = self.run_cwl()

        expected_output = {
            'output_file': {
                'location': 'file://' + os.path.join(output_dir, 'output.maf'),
                'basename': 'output.maf',
                'class': 'File',
                'checksum': 'sha1$fb9f90ada35383f8b74321d0ae8c225a83955539',
                'size': 242,
                'path': os.path.join(output_dir, 'output.maf')
                }
            }
        expected_path = os.path.join(output_dir, 'output.maf')
        self.assertCWLDictEqual(output_json, expected_output)

        comments, mutations = self.load_mutations(expected_path)

        expected_comments = ['# comment 1', '# comment 2']
        self.assertEqual(comments, expected_comments)

        expected_mutations = [ maf_row1, maf_row2 ]
        self.assertEqual(mutations, expected_mutations)

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


class TestPlutoTestCase(PlutoTestCase):
    def test_assertCWLDictEqual(self):
        """
        Test that CWL output dict objects have their keys stripped down to remove inconsistent output fields
        Basic test cases
        """
        d1 = {'a':1, 'nameext': "foo", 'nameroot':'bar'}
        d2 = {'a':1}
        self.assertCWLDictEqual(d1, d2)

        d1 = {'a':1, 'b':[{'c':1, 'nameext': "foo"}]}
        d2 = {'a':1, 'b':[{'c':1}]}
        self.assertCWLDictEqual(d1, d2)

        d1 = {'a':1, 'nameroot':'bar', 'b':[{'c':1, 'nameext': "foo"}, {'d':2}]}
        d2 = {'a':1, 'b':[{'c':1}, {'d':2}]}
        self.assertCWLDictEqual(d1, d2)

    def test_assertCWLDictEqual_1(self):
        """
        Test cases with more complicated CWL output objects
        """
        self.maxDiff = None
        output_file = "foo.txt"
        output_path = os.path.join(self.tmpdir, output_file)
        d1 = {
            'output_file': {
                'location': 'file://' + output_path,
                'basename': output_file,
                'class': 'File',
                'checksum': 'sha1$2513c14c720e9e1ba02bb4a61fe0f31a80f60d12',
                'size': 114008492,
                'nameext': 'txt', # this gets removed by default
                'nameroot': 'foo', # this gets removed by default
                'path':  output_path
                }
            }
        d2 = {
            'output_file': {
                'location': 'file://' + output_path,
                'basename': output_file,
                'class': 'File',
                'path':  output_path,
                'checksum': 'sha1$2513c14c720e9e1ba02bb4a61fe0f31a80f60d12',
                'size': 114008492
                }
            }
        self.assertCWLDictEqual(d1, d2)

    def test_assertCWLDictEqual_related_keys(self):
        """
        Test cases with removal of related keys
        Use "related_keys" to strip some dict fields but only in the presence of other fields
        Real World Use Case: some files have inconsistent size and checksum due to embedded timestamps, etc.,
        so need need to strip those off when doing comparisons
        """
        self.maxDiff = None
        output_file = "foo.txt"
        output_path = os.path.join(self.tmpdir, output_file)

        # in each dict, if basename == output_file, then remove fields size, checksum
        related_keys = [('basename', output_file, ['size', 'checksum'])]

        d1 = {
            'output_file': {
                'location': 'file://' + output_path,
                'basename': output_file,
                'class': 'File',
                'checksum': 'sha1$2513c14c720e9e1ba02bb4a61fe0f31a80f60d12', # this gets removed by related_keys
                'size': 114008492, # this gets removed by related_keys
                'nameext': 'txt', # this gets removed by default
                'nameroot': 'foo', # this gets removed by default
                'path':  output_path
                }
            }
        d2 = {
            'output_file': {
                'location': 'file://' + output_path,
                'basename': output_file,
                'class': 'File',
                'path':  output_path,
                }
            }

        self.assertCWLDictEqual(d1, d2, related_keys = related_keys)



if __name__ == "__main__":
    unittest.main()
