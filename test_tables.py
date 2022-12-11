#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for table IO handling methods from the tools module
"""
import os
import gzip
import unittest
from tools import (
        md5_file,
        PlutoTestCase,
        TableReader,
        write_table,
        load_mutations,
        dicts2lines,
        MafWriter
    )

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


class TestGzIO(PlutoTestCase):
    """
    Test that files in .gz format can be automatically opened and read as tables
    """
    def test_write_read_gz1(self):
        # make a .gz table file
        # NOTE: filename must end with .gz
        gz_file = os.path.join(self.tmpdir, "data.tsv.gz")
        fout = gzip.open(gz_file, "wt")
        lines = [
            ['# comment 1'],
            ['# comment 2'],
            ['Hugo_Symbol', 't_depth', 't_alt_count'],
            ['SUFU', '100', '75'],
            ['GOT1', '100', '1'],
            ['SOX9', '100', '0'],
        ]
        for line in lines:
            l = '\t'.join(line) + '\n'
            fout.write(l)
        fout.close()

        # NOTE: cannot take hash of .gz because the bytes are discrepant between instances!
        # hash = md5_file(gz_file)
        # self.assertEqual(hash, '3a52734d91cc020ff6689b0d13ab53d1')

        # load the mutations; automatically reads from .gz input
        comments, mutations = self.load_mutations(gz_file)

        expected_comments = ['# comment 1', '# comment 2']
        self.assertEqual(comments, expected_comments)

        expected_mutations = [
            {'Hugo_Symbol': 'SUFU', 't_depth': '100', 't_alt_count':'75'},
            {'Hugo_Symbol': 'GOT1', 't_depth': '100', 't_alt_count':'1'},
            {'Hugo_Symbol': 'SOX9', 't_depth': '100', 't_alt_count':'0'}
            ]
        self.assertEqual(mutations, expected_mutations)


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


if __name__ == "__main__":
    unittest.main()
