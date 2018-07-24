'''
Core of package `grython`, providing utilities including:
* `Pattern`: class for parsing CSS selectors and finding HTML elements;
* `require`: function wrapping `requests.get` & `bs4.BeautifulSoup`;
'''

import re
import random

import requests
from bs4 import BeautifulSoup

 # Define constant variables
__all__ = ['Pattern', 'require']

class Pattern:
    '''
    This class can parse a CSS selector into a search pattern:
    * It use a dictionary to represent an HTML element;
    * It has a classmethod `parse` for parsing CSS selectors;
    * It has a method `update` for searching elements in a DOM tree.
    '''

    # Define constant variables
    TAGS = {
        'attrs': r'(?P<attrs>\[([\'"]?)[a-zA-Z][\w-]*\2(=([\'"]?).+?\4)?\])',
        'class': r'(?P<class>\.[\w-]+)',
        'id': r'(?P<id>#[\w-]+)',
        'name': r'(?P<name>[\w-]+)',
        'rank': r'(?P<rank>\[\d+\])'
    }

    def __init__(self, pattern):
        if not isinstance(pattern, str):
            raise TypeError('expected a string object')
        self.__pattern = tuple(Pattern.parse(pattern))
        self.__raw = re.sub(r'\s+', ' ', pattern)

    def __iter__(self):
        return iter(self.pattern)

    def __len__(self):
        return len(self.pattern)

    def __repr__(self):
        return f'<grython.core.Pattern \'{self.__raw}\'>'

    def __str__(self):
        return f'<grython.core.Pattern \'{self.__raw}\'>'

    @classmethod
    def __parse(cls, pattern, recursive=True):
        '''
        A protected method of class `Pattern` that parse single-element patterns like CSS selectors
        '''

        # Initialize variables
        info = {
            'attrs': {},
            'name': '',
            'recursive': recursive
        }
        last_match = None
        parser = re.compile('|'.join(cls.TAGS.values()))
        scanner = parser.scanner(pattern)
        # Start parsing patterns
        for match in iter(scanner.match, None):
            last_match = match
            if match.lastgroup == 'attrs':
                attr = re.sub(r'[\'"\[\]]', '', match.group()).split('=', 1)
                info['attrs'][attr[0]] = True if len(attr) == 1 else attr[1]
            elif match.lastgroup == 'class':
                class_ = match.group().lstrip('.')
                info['attrs'].setdefault('class', []).append(class_)
            elif match.lastgroup == 'id':
                info['attrs']['id'] = match.group().lstrip('#')
            elif match.lastgroup == 'name':
                info['name'] = match.group()
            elif match.lastgroup == 'rank':
                info['rank'] = int(match.group().strip('[]'))
        # Handle illegal patterns
        if last_match is None or last_match.span()[1] != len(pattern):
            raise ValueError('illegal pattern in span {}'.format(last_match.span()))
        return info

    @classmethod
    def parse(cls, pattern):
        '''
        A class-scale method that parses multi-element patterns like CSS selectors
        '''

        elts = re.split(r'\s', pattern)
        for index, elt in enumerate(elts):
            if elts[index] != '>':
                yield cls.__parse(elt, recursive=True if index == 0 \
                                  or elts[index - 1] != '>' else False)

    @property
    def pattern(self):
        '''
        Property `pattern`'s getter
        '''

        return self.__pattern

    @pattern.setter
    def pattern(self, newpat):
        '''
        Property `pattern`'s setter
        '''

        self.__pattern = tuple(Pattern.parse(newpat))

    def update(self, rootnode):
        '''
        Find elements from the rootnode and return as a generator
        '''

        def __update(parentnode, index):
            this = self.pattern[index]
            childnodes = parentnode.find_all(this['name'], attrs=this['attrs'], \
                                             recursive=this['recursive'])
            if index == len(self) - 1:
                if 'rank' in this:
                    if this['rank'] < len(childnodes):
                        yield childnodes[this['rank']]
                else:
                    yield from childnodes
            else:
                if 'rank' in this:
                    if this['rank'] < len(childnodes):
                        yield from __update(childnodes[this['rank']], index + 1)
                else:
                    for childnode in childnodes:
                        yield from __update(childnode, index + 1)

        return __update(rootnode, 0)

def require(url, encoding=None, parse=True, **kwargs):
    '''
    Require and parse html from specific urls with `requests.get` & `bs4.BeautifulSoup`.
    * You can pass `headers`, 'cookies' & 'proxies' to customize your request;
    * You can pass parameter `parse=False` to get a raw response.
    '''

    # Initialize variables
    user_agent = [
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0)',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.9.168 Version/11.52',
        'Opera/9.80 (Windows NT 6.1; WOW64; U; en) Presto/2.10.229 Version/11.62'
    ]
    headers = kwargs['headers'] if 'headers' in kwargs else {}
    if True not in tuple(map(lambda s: s.lower() == 'user-agent', headers)):
        headers.update({'User-Agent': random.choice(user_agent)})
    cookies = kwargs['cookies'] if 'cookies' in kwargs else None
    proxies = kwargs['proxies'] if 'proxies' in kwargs else None
    # Start HTTP requests
    resp = requests.get(url, headers=headers, cookies=cookies, proxies=proxies)
    try:
        resp.raise_for_status()
    except requests.HTTPError as error:
        print(error)
        return 0
    if encoding:
        resp.encoding = encoding
    # Return raw response if not ot parse
    if not parse:
        return resp
    # Start parsing html content and return parsed
    soup = BeautifulSoup(resp.content, 'html.parser', from_encoding=resp.encoding)
    return soup
