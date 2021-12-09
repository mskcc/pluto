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

This reduces the total size of the final output JSON representation used in test case code to 20% or less of the original JSON format

"""
# https://stackoverflow.com/questions/44640479/mypy-annotation-for-classmethod-returning-instance
from __future__ import annotations # python 3.7-3.9, not needed in 3.10
import os
import sys
import json
from copy import deepcopy
from typing import List
from urllib.parse import urlparse, urlsplit, urlunsplit

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

        # use these for custom repr method
        self.args = ()
        self.kwargs = {}

    @classmethod
    def init(cls, *args, **kwargs) -> OFile:
        """
        Initialize an instance of OFile but retain the args that were passed
        Need this for repr()
        """
        obj = cls(*args, **kwargs)
        obj.args = args
        obj.kwargs = kwargs
        return(obj)

    @classmethod
    def init_dict(cls, d: Dict, in_subdir: bool = False, *args, **kwargs) -> OFile:
        """
        Initialize an instance of OFile automatically from a Python dict

            d = {'location': 'file:///output/Sample1.maf', 'basename': 'Sample1.maf', 'nameroot': 'Sample1', 'nameext': '.maf', 'class': 'File', 'checksum': 'sha1$12345', 'size': 108887494}
        """
        name = d['basename'] # this one is required
        # all these are optional
        size = d.get('size', None)
        hash = d.get('checksum', None) # x.startswith('sha1$')
        class_label = d.get('class', None)
        location = d.get('location', None) # file:///output/Sample1.maf
        dir = None
        location_base = None
        location_parts = None

        # get the location_base from the location
        if location:
            location_parts = urlsplit(location)
            # SplitResult(scheme='file', netloc='', path='/output/Sample1.maf', query='', fragment='')
            location_base = urlunsplit([location_parts.scheme, location_parts.netloc, '', '', '']) # file://

            # if the OFile is not in a subdir, we can initialize it with a 'dir'
            if not in_subdir:
                dir = os.path.dirname(location_parts.path)

        # remove prefix that might be pre-pended onto the hash
        hash_prefix = 'sha1$'
        if str(hash).startswith(hash_prefix):
            hash = hash[len(hash_prefix):]

        init_kwargs = {}
        init_kwargs['name'] = name
        if size:
            init_kwargs['size'] = size
        if hash:
            init_kwargs['hash'] = hash
        if class_label and class_label != 'File': # dont include if its just using the default value
            init_kwargs['class_label'] = class_label
        if dir:
            init_kwargs['dir'] = dir
        if location_base and location_base != 'file://': # dont include if its just using the default value
            init_kwargs['location_base'] = location_base

        f = cls.init(*args, **kwargs, **init_kwargs)
        return(f)

    def repr(self) -> str:
        """
        Generate a text representation of the object that can be used to recreate the object
        Only works if object was created with `init`
        """
        n = 'OFile('
        if self.args:
            for i, arg in enumerate(self.args):
                n += arg.__repr__()
                if i < len(self.args) - 1 or self.kwargs:
                    n += ', '
        if self.kwargs:
            for i, (k, v) in enumerate(self.kwargs.items()):
                n += str(k) + '=' + v.__repr__()
                if i < len(self.kwargs.items()) - 1:
                    n += ', '
        n += ')'
        return(n)

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

        # use these for custom repr method
        self.args = ()
        self.kwargs = {}

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

    @classmethod
    def init(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        obj.args = args
        obj.kwargs = kwargs
        return(obj)

    @classmethod
    def init_dict(cls, d: Dict, in_subdir: bool = False, *args, **kwargs) -> ODir:
        """
        Initialize an instance of ODir automatically from a Python dict

            {'class': 'Directory', 'basename': 'analysis', 'listing': [{'location': 'file:///output/analysis/cna.txt', 'basename': 'cna.txt', 'nameroot': 'cna', 'nameext': '.txt', 'class': 'File', 'checksum': 'sha1$1234', 'size': 6547460}], 'location': 'file:///output/analysis'}
        """
        name = d['basename'] # this one is required
        items = d['listing'] # this one is required
        # all these are optional
        class_label = d.get('class', None)
        location = d.get('location', None) # file:///output/analysis
        dir = None
        location_base = None
        location_parts = None

        # get the location_base from the location
        if location:
            location_parts = urlsplit(location)
            # SplitResult(scheme='file', netloc='', path='/output/Sample1.maf', query='', fragment='')
            location_base = urlunsplit([location_parts.scheme, location_parts.netloc, '', '', '']) # file://

            # if the ODir is not in a subdir, we can initialize it with a 'dir'
            if not in_subdir:
                dir = os.path.dirname(location_parts.path)

        # need to initialize all the listing items
        new_items = []
        for item in items:
            if item['class'] == 'File':
                i = OFile.init_dict(item, in_subdir = True)
                new_items.append(i)
            elif item['class'] == 'Directory':
                i = ODir.init_dict(item, in_subdir = True)
                new_items.append(i)

        init_kwargs = {}
        init_kwargs['name'] = name
        init_kwargs['items'] = new_items
        if class_label and class_label != 'Directory': # dont include if its just using the default value
            init_kwargs['class_label'] = class_label
        if dir:
            init_kwargs['dir'] = dir
        if location_base and location_base != 'file://': # dont include if its just using the default value
            init_kwargs['location_base'] = location_base

        odir = cls.init(*args, **kwargs, **init_kwargs)
        return(odir)

    @staticmethod
    def repr_list(args, has_next = None):
        r = ''
        for i, arg in enumerate(args):
            if hasattr(arg, 'repr'):
                r += arg.repr()
            else:
                r += arg.__repr__()
            if i < len(args) - 1 or has_next:
                r += ', '
        return(r)

    def repr(self):
        """
        Generate a text representation of the object that can be used to recreate the object
        Only works if object was created with `init`
        """
        n = 'ODir('
        if self.args:
            n += self.repr_list(self.args, self.kwargs)
        if self.kwargs:
            for i, (k, v) in enumerate(self.kwargs.items()):
                n += str(k) + '='
                if isinstance(v, list):
                    n += '['
                    n += self.repr_list(v) + ']'
                else:
                    n += v.__repr__()
                if i < len(self.kwargs.items()) - 1:
                    n += ', '
        n += ')'
        return(n)





# command line interface
if __name__ == '__main__':
    """
    Usage
        $ python3 serializer.py ../output.json | sed -e 's|OFile|\nOFile|g' -e 's|ODir|\nODir|g'
    """
    args = sys.argv[1:]
    input_json = args[0]

    # load the input JSON file
    with open(input_json) as fin:
        data = json.load(fin)

    # convert all the entries into OFile and ODir object text representations
    new_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            if value['class'] == 'File':
                obj = OFile.init_dict(value)
                new_data[key] = obj.repr()
            elif value['class'] == 'Directory':
                obj = ODir.init_dict(value)
                new_data[key] = obj.repr()
        else:
            # TODO: what to do here??
            new_data[key] = value
    # TODO: this still outputs with quotes around the repr's and also does not indent at all,
    # not sure how to handle that but its close enough for now
    print(new_data)
