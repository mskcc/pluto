"""
module for creating a Python object to represent the CWL command line output and then serialize it to/from a JSON

CWL output is essentially a JSON dict representing workflow output entries

Need an easy, concise way to build an "expected" output object
so we can compare it against a real output JSON easily
"""
import os
from copy import deepcopy
from typing import List

class OFile(dict):
    """
    Output File object

    Example JSON representation;

    {'basename': 'Sample4_purity.seg',
     'checksum': 'sha1$e6df130c57ca594578f9658e589cfafc8f40a56c',
     'class': 'File',
     'location': 'file://' + os.path.join(output_dir,'Sample4_purity.seg'),
     'path': os.path.join(output_dir,'Sample4_purity.seg'),
     'size': 488}
    """
    def __init__(self, name: str, dir: str = None, size: int = None, hash: str = None, location_base: str = 'file://', class_label: str = 'File'):
        self['basename'] = name
        self['class'] = class_label
        if dir:
            self['path'] = os.path.join(dir, self['basename'])
        else:
            self['path'] = self['basename'] # TODO: should this be prefixed with '/' or pwd? dont think it will actually come up in real life use cases
        self['location'] = location_base + self['path']
        if size:
            self['size'] = size
        if hash:
            self['checksum'] = 'sha1$' + hash

class ODir(dict):
    """
    Output Directory Object

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
    """
    def __init__(self, dir: str, name: str, items: List[OFile], location_base: str = 'file://', class_label: str = 'Directory'):
        self['basename'] = name
        self['class'] = class_label
        self['path'] = os.path.join(dir, self['basename'])
        self['location'] = location_base + self['path']
        self['listing'] = []
        for item in items:
            i = deepcopy(item)
            i['path'] = os.path.join(self['path'], i['path'])
            i['location'] = location_base + i['path']
            self['listing'].append(i)
