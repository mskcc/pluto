#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unit tests for the tools module
"""
import os
import unittest
from tempfile import TemporaryDirectory

# relative imports, from CLI and from parent project
if __name__ != "__main__":
    from .tools import md5_file, PlutoTestCase, CWLFile

if __name__ == "__main__":
    from tools import md5_file, PlutoTestCase, CWLFile

class TestMd5(unittest.TestCase):
    def test_md5(self):
        with TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "file.txt")
            lines = ['foo', 'bar']
            with open(filename, "w") as fout:
                for line in lines:
                    fout.write(line + '\n')
            hash = md5_file(filename)
            self.assertEqual(hash, 'f47c75614087a8dd938ba4acff252494')


class TestCopyCWL(PlutoTestCase):
    CWL_DIR = os.path.abspath('cwl')
    cwl_file = CWLFile('copy.cwl', CWL_DIR = CWL_DIR)
    def test_copy(self):
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
        self.assertDictEqual(output_json, expected_output)

        comments, mutations = self.load_mutations(output_json['output_file']['path'])

        expected_comments = ['# comment 1', '# comment 2']
        self.assertEqual(comments, expected_comments)

        expected_mutations = [
            {'Hugo_Symbol': 'SUFU', 't_depth': '100', 't_alt_count':'75'},
            {'Hugo_Symbol': 'GOT1', 't_depth': '100', 't_alt_count':'1'},
            {'Hugo_Symbol': 'SOX9', 't_depth': '100', 't_alt_count':'0'}
            ]
        self.assertEqual(mutations, expected_mutations)

if __name__ == "__main__":
    unittest.main()
