#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import os
import unittest
from serializer import OFile
from plutoPreRunTestCase import PlutoPreRunTestCase
from tools import (
        CWLFile,
    )

class TestPlutoPreRunTestCase(PlutoPreRunTestCase):
    cwl_file = CWLFile('copy.cwl', CWL_DIR = os.path.abspath('cwl'))

    def setUpRun(self):
        """
        This will get called ONCE during test setup to run the pipeline
        """
        lines = [
            ['# comment 1'],
            ['# comment 2'],
            ['Hugo_Symbol', 't_depth', 't_alt_count'],
            ['SUFU', '100', '75'],
            ['GOT1', '100', '1'],
            ['SOX9', '100', '0'],
        ]
        input = self.write_table(tmpdir = self.tc.tmpdir, filename = 'input.maf', lines = lines)

        self.input = {
            "input_file": {
                  "class": "File",
                  "path": input
                },
            "output_filename":  'output.maf',
            }
        output_json, output_dir = self.run_cwl()
        return(output_json, output_dir)

    def getExpected(self, output_dir):
        return({"output_file": OFile(
            name = "output.maf",
            dir = output_dir,
            size = 90,
            hash = '7bcfa105aa117881f032765595bec2e9a016a1e7')})

    def test_foo1(self):
        self.assertEqual(
                self.res.output['output_file']['checksum'],
                self.res.expected['output_file']['checksum'])

    def test_bar1(self):
        self.assertCWLDictEqual(self.res.output, self.res.expected)

    def test_baz1(self):
        self.assertNumMutationsHash(
            OFile.init_dict(self.res.output['output_file']).path,
            3, '27e9aa95e80f808553624eb7522622f8')

    def test_foo2(self):
        self.assertMutFieldContains(
            OFile.init_dict(self.res.output['output_file']).path,
            "Hugo_Symbol", ["SUFU", "GOT1", "SOX9"], containsAll = True)

    def test_bar2(self):
        self.assertMutFieldDoesntContain(
            OFile.init_dict(self.res.output['output_file']).path,
            "Hugo_Symbol", [""])


if __name__ == "__main__":
    unittest.main()
