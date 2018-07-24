# Grython

## Introduction

Package *grython* is a *light* weight python crawler framework. It is designed for daily work, extracting articles or images for instance. The main features of *grython* are:

1. Package *grython* only depends on *requests* & *beautifulsoup*, which means in most cases you are able to stay lighter and less complex than *scrapy*;
2. Package *grython* supporta CSS selectors. Extracting contents from HTML here is easier than you think;

Though *grython* is designed to be light, it could perfectly handle some larger projects as well.

## Installation

You can easily install with `pip install grython`.

## Usage

Here a minimium example is given. The scene may seem familiar: you're hooked on the novel [*Desolate Era*](https://www.wuxiaworld.com/novel/desolate-era), you want to get a ebook copy in your local storage. Of course manually copying and pasting will be troublesome, but with *grython* all the problem can be resolved with a few short commands. For instance:
```python
import grython

# Collecting links for each chapter
url = 'https://www.wuxiaworld.com/novel/desolate-era'
soup = grython.require(url, encoding='utf-8')
pattern = grython.Pattern('li.chapter-item a')
hrefs = ['https://www.wuxiaworld.com' + elt['href'] for elt in pattern.update(soup)]

# Download extracted contents
recipe = grython.Recipe('desolate-era', {
    'title': 'h4[1]',
    'content': 'div.fr-view'
})
for href in hrefs:
    soup = grython.require(href, encoding='utf-8')
    recipe.extract_txt(soup)
    print(f'url {href} extracted!')
```
And now all you have to do is counting on your fingers!  
But *grython* has some more functions than that. For example:  
* Cutomize proxies, headers and cookies for `grython.require`;
* Different data formats including `json`, `xml`, `txt` and `db` for `grython.Recipe`.

## Limitation

* Documents in detail remain to be written;
* Threading security is not guaranteed;
* No proper exception processing: one exception may cause the entire crawler to collapse.

Problems above will be resolved as soon as possible.
