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


class TestTableHandlers(PlutoTestCase):
    def test_write_read_lines(self):
        """
        Make sure that lines are written out to file correctly
        Should be no carriage returns
        """
        lines = [
            ['# comment 1'],
            ['# comment 2'],
            ['Hugo_Symbol', 't_depth', 't_alt_count'],
            ['SUFU', '100', '75'],
            ['GOT1', '100', '1'],
            ['SOX9', '100', '0'],
        ]

        input_path = write_table(tmpdir = self.tmpdir, filename = 'input.maf', lines = lines)

        with open(input_path) as f:
            lines = [ l for l in f]

        expected_lines = [
            '# comment 1\n',
            '# comment 2\n',
            'Hugo_Symbol\tt_depth\tt_alt_count\n',
            'SUFU\t100\t75\n',
            'GOT1\t100\t1\n',
            'SOX9\t100\t0\n']

        self.assertEqual(lines, expected_lines)

        hash = md5_file(input_path)
        self.assertEqual(hash, '584d00e49b0bd7f963af1db46a61d2f0')

    def test_TableReader1(self):
        """
        Test that table is read correctly
        """
        maf_lines = [
        '# comment 1\n',
        '# comment 2\n',
        'Hugo_Symbol\tt_depth\tt_alt_count\n',
        'SUFU\t100\t75\n',
        'GOT1\t100\t1\n',
        'SOX9\t100\t0\n'
        ]
        input_maf_file = os.path.join(self.tmpdir, "data.txt")
        with open(input_maf_file, "w") as fout:
            for line in maf_lines:
                fout.write(line)

        hash = md5_file(input_maf_file)
        self.assertEqual(hash, '584d00e49b0bd7f963af1db46a61d2f0')

        table_reader = TableReader(input_maf_file)
        comments = table_reader.comment_lines
        fieldnames = table_reader.get_fieldnames()
        records = [ rec for rec in table_reader.read() ]

        expected_comments = ['# comment 1\n', '# comment 2\n']
        self.assertEqual(comments, expected_comments)

        expected_fieldnames = ['Hugo_Symbol', 't_depth', 't_alt_count']
        self.assertEqual(fieldnames, expected_fieldnames)

        expected_records = [
            dict([('Hugo_Symbol', 'SUFU'), ('t_depth', '100'), ('t_alt_count', '75')]),
            dict([('Hugo_Symbol', 'GOT1'), ('t_depth', '100'), ('t_alt_count', '1')]),
            dict([('Hugo_Symbol', 'SOX9'), ('t_depth', '100'), ('t_alt_count', '0')])
            ]
        self.assertEqual(records, expected_records)

    def test_TableReader_without_comments(self):
        """
        Test that table without comments is read correctly
        """
        maf_lines = [
        'Hugo_Symbol\tt_depth\tt_alt_count\n',
        'SUFU\t100\t75\n',
        'GOT1\t100\t1\n',
        'SOX9\t100\t0\n'
        ]
        input_maf_file = os.path.join(self.tmpdir, "data.txt")
        with open(input_maf_file, "w") as fout:
            for line in maf_lines:
                fout.write(line)

        hash = md5_file(input_maf_file)
        self.assertEqual(hash, '0906f811a2255324fd4beeb960c53894')

        table_reader = TableReader(input_maf_file)
        comments = table_reader.comment_lines
        fieldnames = table_reader.get_fieldnames()
        records = [ rec for rec in table_reader.read() ]

        expected_comments = []
        self.assertEqual(comments, expected_comments)

        expected_fieldnames = ['Hugo_Symbol', 't_depth', 't_alt_count']
        self.assertEqual(fieldnames, expected_fieldnames)

        expected_records = [
            dict([('Hugo_Symbol', 'SUFU'), ('t_depth', '100'), ('t_alt_count', '75')]),
            dict([('Hugo_Symbol', 'GOT1'), ('t_depth', '100'), ('t_alt_count', '1')]),
            dict([('Hugo_Symbol', 'SOX9'), ('t_depth', '100'), ('t_alt_count', '0')])
            ]
        self.assertEqual(records, expected_records)

    def test_test_TableReader_ignore_comments(self):
        """
        Make sure that the table can be read correctly when comments are ignored
        Some files have massive comments sections that we shouldn't bother reading
        """
        maf_lines = [
        '# comment 1\n',
        '# comment 2\n',
        'Hugo_Symbol\tt_depth\tt_alt_count\n',
        'SUFU\t100\t75\n',
        'GOT1\t100\t1\n',
        'SOX9\t100\t0\n'
        ]
        input_maf_file = os.path.join(self.tmpdir, "data.txt")
        with open(input_maf_file, "w") as fout:
            for line in maf_lines:
                fout.write(line)

        table_reader = TableReader(input_maf_file, ignore_comments = True)
        comments = table_reader.comment_lines
        fieldnames = table_reader.get_fieldnames()
        records = [ rec for rec in table_reader.read() ]

        expected_comments = []
        self.assertEqual(comments, expected_comments)

        expected_fieldnames = ['Hugo_Symbol', 't_depth', 't_alt_count']
        self.assertEqual(fieldnames, expected_fieldnames)

        expected_records = [
            dict([('Hugo_Symbol', 'SUFU'), ('t_depth', '100'), ('t_alt_count', '75')]),
            dict([('Hugo_Symbol', 'GOT1'), ('t_depth', '100'), ('t_alt_count', '1')]),
            dict([('Hugo_Symbol', 'SOX9'), ('t_depth', '100'), ('t_alt_count', '0')])
            ]
        self.assertEqual(records, expected_records)



    def test_load_mutations1(self):
        """
        Make sure that mutations are loaded correctly from a maf file
        """
        maf_lines = [
        '# comment 1\n',
        '# comment 2\n',
        'Hugo_Symbol\tt_depth\tt_alt_count\n',
        'SUFU\t100\t75\n',
        'GOT1\t100\t1\n',
        'SOX9\t100\t0\n'
        ]
        input_maf_file = os.path.join(self.tmpdir, "data.txt")
        with open(input_maf_file, "w") as fout:
            for line in maf_lines:
                fout.write(line)

        hash = md5_file(input_maf_file)
        self.assertEqual(hash, '584d00e49b0bd7f963af1db46a61d2f0')

        comments, mutations = load_mutations(input_maf_file)

        expected_comments = ['# comment 1', '# comment 2']
        self.assertEqual(comments, expected_comments)

        expected_mutations = [
            {'Hugo_Symbol': 'SUFU', 't_depth': '100', 't_alt_count':'75'},
            {'Hugo_Symbol': 'GOT1', 't_depth': '100', 't_alt_count':'1'},
            {'Hugo_Symbol': 'SOX9', 't_depth': '100', 't_alt_count':'0'}
            ]
        self.assertEqual(mutations, expected_mutations)

    def test_dicts2lines(self):
        """
        Make sure that a list of dicts are converted to a list of lines correctly for writing with write_table
        """
        comments = [['# comment 1'], ['# comment 2']]
        row1 = { 'a':'1', 'b':'2' }
        row2 = { 'a':'6', 'b':'7' }

        lines = dicts2lines(dict_list = [row1, row2], comment_list = comments)

        expected_lines = [['# comment 1'], ['# comment 2'], ['a', 'b'], ['1', '2'], ['6', '7']]

        self.assertEqual(lines, expected_lines)

        input_path = write_table(tmpdir = self.tmpdir, filename = 'input.maf', lines = lines)

        with open(input_path) as f:
            lines = [ l for l in f]

        expected_lines = [
            '# comment 1\n',
            '# comment 2\n',
            'a\tb\n',
            '1\t2\n',
            '6\t7\n'
            ]

        self.assertEqual(lines, expected_lines)

        hash = md5_file(input_path)

        self.assertEqual(hash, '7180052ec5b7f215a8c0eb263b474618')


class TestMafWriter(PlutoTestCase):
    def test_MafWriter1(self):
        """
        Check that MafWriter creates a file identical to the example input
        """
        # create dummy input maf file
        maf_lines = [
        '# comment 1\n',
        '# comment 2\n',
        'Hugo_Symbol\tt_depth\tt_alt_count\n',
        'SUFU\t100\t75\n',
        'GOT1\t100\t1\n',
        'SOX9\t100\t0\n'
        ]
        input_maf_file = os.path.join(self.tmpdir, "data.txt")
        with open(input_maf_file, "w") as fout:
            for line in maf_lines:
                fout.write(line)

        hash = md5_file(input_maf_file)
        self.assertEqual(hash, '584d00e49b0bd7f963af1db46a61d2f0')

        # read the maf file
        reader = TableReader(input_maf_file)
        comments = reader.comment_lines
        fieldnames = reader.get_fieldnames()

        # write out a new copy of the maf file
        output_file = os.path.join(self.tmpdir, "output.txt")
        with open(output_file, "w") as fout:
            writer = MafWriter(fout, fieldnames = fieldnames, comments = comments)
            writer.writeheader()
            for row in reader.read():
                writer.writerow(row)

        hash = md5_file(output_file)
        self.assertEqual(hash, '584d00e49b0bd7f963af1db46a61d2f0')









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
        if CWL_ENGINE == 'toil':
            expected_output['output_file']['nameext'] = '.maf'
            expected_output['output_file']['nameroot'] = 'output'
            expected_output['output_file'].pop('path')
        expected_path = os.path.join(output_dir, 'output.maf')
        self.assertDictEqual(output_json, expected_output)

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
        if CWL_ENGINE == 'toil':
            expected_output['output_file']['nameext'] = '.maf'
            expected_output['output_file']['nameroot'] = 'output'
            expected_output['output_file'].pop('path')
        expected_path = os.path.join(output_dir, 'output.maf')
        self.assertDictEqual(output_json, expected_output)

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
        d1 = {'a':1, 'nameext': "foo", 'nameroot':'bar'}
        d2 = {'a':1}
        self.assertCWLDictEqual(d1, d2)

        d1 = {'a':1, 'b':[{'c':1, 'nameext': "foo"}]}
        d2 = {'a':1, 'b':[{'c':1}]}
        self.assertCWLDictEqual(d1, d2)

        d1 = {'a':1, 'nameroot':'bar', 'b':[{'c':1, 'nameext': "foo"}, {'d':2}]}
        d2 = {'a':1, 'b':[{'c':1}, {'d':2}]}
        self.assertCWLDictEqual(d1, d2)

if __name__ == "__main__":
    unittest.main()
