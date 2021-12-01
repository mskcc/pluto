"""
module for creating a Python object to represent the CWL command line output, which can be easily serialized to JSON and/or a Python dict

CWL output is essentially a JSON dict representing workflow output entries

Need an easy, concise way to build an "expected" output object
so we can compare it against a real output JSON easily

When writing test cases for CWL's, storing the expected output CWL JSON becomes
extremely verbose, because some CWL's can have numerous outputs, each with dynamically
updated output temp path

This module's classes aim to help reduce the amount of code needed to represent
the CWL output in Python

for example, some pluto test cases have 1000's of lines, most of which is CWL JSON representation

The goal of these methods is to have the shortest class names, args, methods, etc., possible to easily create and convey the meaning of test case items, and still be compatible with the
built-in unittest.TestCase assertions


So hopefully we can reduce something like this;

    expected_output = {
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

Down to something like this;

    expected_output = ODir(name = 'portal', dir = tmpdir, items = [
        OFile(size = 488, name = 'Sample4_purity.seg', hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
    ])

And still use this;

    self.assertDictEqual(output_json, expected_output)
    self.assertEqual(output_json, expected_output)

"""
import os
from copy import deepcopy
from typing import List

class OFile(dict):
    """
    Output File object

    IMPORTANT: when OFile is inside a subdir, initialize with dir = None (the default value) !!

    Example JSON representation;

    {'basename': 'Sample4_purity.seg',
     'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
     'class': 'File',
     'location': 'file://' + os.path.join(output_dir,'Sample4_purity.seg'),
     'path': os.path.join(output_dir,'Sample4_purity.seg'),
     'size': 488}

    Example usage;

        >>> OFile(size = 488, name = 'Sample4_purity.seg', dir = tmpdir, hash = 'e6df130c57ca594578f9658e589cfafc8f40a56c')
    """
    def __init__(self,
        name: str, # the basename of the file
        dir: str = None, # the parent dir path if OFile is **not** in a workflow subdir
        size: int = None, # the size of the file in bytes
        hash: str = None, # the sha1 hash of the file
        location_base: str = 'file://',
        class_label: str = 'File'
        ):
        self['basename'] = name
        self['class'] = class_label
        # set path and location as object attributes because we need special handling for their dict keys later
        # NOTE: I removed ^^^ that logic btw
        if dir:
            self.path = os.path.join(dir, self['basename'])
        else:
            self.path = self['basename'] # TODO: should this be prefixed with '/' or pwd? dont think it will actually come up in real life use cases
        self.location = location_base + self.path

        if size:
            self['size'] = size
        if hash:
            self['checksum'] = 'sha1$' + hash

        self['location'] = self.location
        self['path'] = self.path

class ODir(dict):
    """
    Output Directory Object

    NOTE: IMPORTANT: when ODir is a subdir, initialize with dir = None (the default value) !!

    TODO: find a way to implement this so that both OFile and ODir do not have so much duplicated code

    Example JSON representation;

    'portal_dir': {
        'location': 'file://' + os.path.join(output_dir, 'portal'),
        'path': os.path.join(output_dir, 'portal'),
        'class': 'Directory',
        'basename': 'portal',
        'listing': [
            {
                'location': 'file://' + os.path.join(output_dir, 'portal/meta_clinical_sample.txt'),
                'basename': 'meta_clinical_sample.txt',
                'class': 'File',
                'checksum': 'sha1$7d2bb282e74ff6a5d41b334ded689f9336722702',
                'size': 132,
                'path': os.path.join(output_dir, 'portal/meta_clinical_sample.txt')
            }
            ]

    Example usage;

        >>> expected_output = {
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
    """
    def __init__(self,
        name: str, # the basename of the directory
        items: List[OFile], # the list of ODir or OFile items inside the dir
        dir: str = None, # the parent dir path, if ODir is **not** a subdir
        location_base: str = 'file://',
        class_label: str = 'Directory'
        ):
        self['basename'] = name
        self['class'] = class_label

        # set path and location as object attributes because we need special handling for their dict keys later
        # if a dir was passed, update the path and location to prepend it
        if dir:
            self.path = os.path.join(dir, self['basename'])
        else:
            self.path = self['basename'] # TODO: should this be prefixed with '/' or pwd? dont think it will actually come up in real life use cases
        self.location = location_base + self.path


        self['location'] = self.location
        self['path'] = self.path

        # update the path and location entries for all contents
        self['listing'] =[ i for i in self.update_listings(base_path = self.path, items = items) ]

    def update_listings(self, base_path: str, items: List[OFile], location_base: str = 'file://') -> OFile:
        """
        Recursively adds entries with correct 'path' and 'location' fields to the
        current instance's 'listing'
        updates the 'listing' for all sub-items as well in order to pre-pend the correct base_path to all 'path' and 'location' fields
        """
        for item in items:
            i = deepcopy(item) # need a copy because we are dealing with mutable objects; WARNING: this could have bad memory implications for some massive object but we usually dont see that in test cases...
            i.path = os.path.join(base_path, i.path)
            i.location = location_base + i.path
            if 'path' in i.keys():
                i['path'] = i.path
            if 'location' in i.keys():
                i['location'] = i.location
            if 'listing' in i:
                i['listing'] = [ q for q in self.update_listings(base_path = base_path, items = i['listing'], location_base = location_base) ]

            yield(i)
