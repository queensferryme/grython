'''
Useful utilities for managing your scraped contents, including:
* image: download a single image from an url;
* images: download multiple images from a list of urls；
* Recipe: extract information with recipes and store in specific formats.
'''

import json
import os
import re
import sqlite3
from collections import Iterable
from xml.dom.minidom import Document, parse

from . import core

__all__ = ['image', 'images', 'Recipe']

class Recipe:
    '''
    This class extracts information and stores it in specific formats according to recipes
    '''

    def __init__(self, name, recipe, raw=False):
        self.name = name
        self.raw = bool(raw)
        # Preprocess recipe dictionary
        for key, value in recipe.items():
            recipe[key] = {}
            if isinstance(value, Iterable) and len(value) == 2:
                if not callable(value[1]):
                    raise TypeError('expected a callable object')
                recipe[key]['pattern'] = core.Pattern(value[0])
                recipe[key]['func'] = value[1]
            else:
                recipe[key]['pattern'] = core.Pattern(value)
        self.recipe = recipe

    def __str__(self):
        return f'<grython.utils.Recipe \'{self.name}\'>'

    def __repr__(self):
        return f'<grython.utils.Recipe \'{self.name}\'>'

    def _extract(self, rootnode):
        '''
        Extract values with recipes from a parsed DOM tree
        '''

        values = dict.fromkeys(self.recipe)
        for key, value in self.recipe.items():
            elts = value['pattern'].update(rootnode)
            if 'func' in value:
                func = value['func']
            elif self.raw:
                func = str
            else:
                func = lambda e: e.get_text()
            values[key] = list(map(func, elts))
        return values

    def extract_json(self, rootnodes, name=None):
        '''
        Store extracted information in a json file.\n
        You are expected to provide a list of rootnodes instead of a single one
        to reduce duplicate loading and dumping json strings.\n
        In the meanwhile, please pay attention to internal memory overflow.
        '''

        def __generator():
            for rootnode in rootnodes:
                yield self._extract(rootnode)

        # Initialize variables
        filename = f'{name or self.name}.json'
        list_of_values = list(__generator())
        if not os.path.exists(filename):
            with open(filename, 'wt', encoding='utf-8') as fout:
                fout.write('{"items":[]}')
        with open(filename, 'rt', encoding='utf-8') as fin:
            local = fin.read()
        # Try to load local json information
        try:
            local = json.loads(local)
        # Handle corrupted or empty json files
        except json.JSONDecodeError:
            with open(filename, 'wt', encoding='utf-8') as fout:
                fout.write(json.dumps({
                    'items': list_of_values
                }, ensure_ascii=False, indent=4))
        # Merge with existed json information
        else:
            if 'items' not in local or not isinstance(local['items'], list):
                local['items'] = []
            local['items'].extend(list_of_values)
            with open(filename, 'wt', encoding='utf-8') as fout:
                fout.write(json.dumps(local, ensure_ascii=False, indent=4))

    def extract_sql(self, rootnode, name=None):
        '''
        Store extracted information in a database file.\n
        The keys are arranged in a dictionary order.
        '''

        # Initialize environment
        tablename = name or self.name
        conn = sqlite3.connect(f'{self.name}.db')
        cur = conn.cursor()
        cur.execute(f'''CREATE TABLE IF NOT EXISTS {tablename} (
            {', '.join(f'{key} TEXT' for key in sorted(self.recipe))}
        );''')
        # Inserting new values
        values = self._extract(rootnode)
        for key, value in values.items():
            values[key] = str(*value) if len(value) <= 1 else str(value)
        cur.execute(f'''INSERT INTO {tablename} VALUES (
            {', '.join('?' for _ in values)}
        );''', [values[key] for key in sorted(values)])
        # Commit & close database
        conn.commit()
        conn.close()

    def extract_txt(self, rootnode, name=None, **kwargs):
        '''
        Store extracted information in a text file.\n
        You have three optional key word arguments:\n
        * sep: indicating a seperating string between sessions;
        * repl: a dictionary to replace key with value, regexp supported;
        * write_keys: whether to write uppercase key words.
        '''

        # Initialize variables
        filename = name or self.name
        values = self._extract(rootnode)
        repl = kwargs['repl'] if 'repl' in kwargs else {}
        sep = kwargs['sep'] if 'sep' in kwargs else ''
        # Writing text contents
        with open(f'{filename}.txt', 'at', encoding='utf-8') as fout:
            for key, value in values.items():
                if 'write_keys' in kwargs and kwargs['write_keys']:
                    fout.write(f'{key.upper()}:\n')
                for each in value:
                    # Hanlde replacements
                    for pattern, result in repl.items():
                        each = re.sub(pattern, result, each)
                    fout.write(f'{each}\n')
            fout.write(f'{sep}\n')

    def extract_xml(self, rootnodes, name=None):
        '''
        Store extracted information in an xml file.\n
        You are expected to provide a list of rootnodes instead of a single one
        to reduce duplicate parsing xml strings.\n
        '''

        def __generator():
            for rootnode in rootnodes:
                yield self._extract(rootnode)

        # Initialize variables
        filename = f'{name or self.name}.xml'
        if os.path.exists(filename):
            doc = parse(filename)
        else:
            doc = Document()
            root = doc.createElement(f'{name or self.name}')
            doc.appendChild(root)
        root = doc.firstChild
        list_of_values = __generator()
        # Append new elements
        for values in list_of_values:
            item = doc.createElement('item')
            for key, value in values.items():
                key = doc.createElement(str(key))
                for each in value:
                    key.appendChild(doc.createElement('text') \
                                    .appendChild(doc.createTextNode(str(each))))
                item.appendChild(key)
            root.appendChild(item)
        # Write xml files
        with open(filename, 'wt', encoding='utf-8') as fout:
            doc.writexml(fout, indent=' '*4, addindent=' '*4, newl='\n', encoding='utf-8')

def image(url, directory='.', name=None, fmt=None, verbose=False, **kwargs):
    '''
    This function downloads an image from a spcific url.
    '''

    # Initialize a file name and a format according to urls
    match = re.search(r'(?P<name>[\w-]{,10})\.(?P<fmt>[a-zA-Z]{3,4})$', url)
    name = (match.group('name') if match else 'image') if not name else name
    fmt = (match.group('fmt') if match else 'png') if not fmt else fmt
    # Change current working directory
    if not os.path.exists(directory):
        os.mkdir(directory)
    os.chdir(directory)
    # Start an HTTP request
    resp = core.require(url, parse=False, **kwargs)
    try:
        resp.raise_for_status()
    except core.requests.HTTPError as error:
        print(error)
    if verbose:
        print('processing images at {},\n status: {}, content_length: {}...' \
              .format(url, resp.status_code, len(resp.content)))
    # Store bytes in an image file
    with open(f'{name}.{fmt}', 'wb') as fout:
        fout.write(resp.content)
    return len(resp.content)

def images(urls, directory='.', rename=False, fmt=None, verbose=True, **kwargs):
    '''
    This function downloads images from specific urls with function `image`
    '''

    for index, url in enumerate(urls, 1):
        if not rename:
            name = None
        elif rename is True:
            name = '{:>3d}'.format(index)
        else:
            name = rename.format(index)
        image(url, directory=directory, name=name, fmt=fmt, verbose=verbose, **kwargs)
