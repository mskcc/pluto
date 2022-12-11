#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for the tools module
"""
import os
import unittest
import shutil
from tools import (
    md5_file,
    md5_obj,
    PlutoTestCase,
    CWLFile,
    write_table,
    load_mutations
)

class TestMd5(PlutoTestCase):
    def test_md5_file(self):
        """
        Test case for getting the md5 of a file
        """
        filename = os.path.join(self.tmpdir, "file.txt")
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
