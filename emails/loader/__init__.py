# encoding: utf-8
import os
import os.path

def from_url(url, **kwargs):
    from .loaders import URLLoader
    loader = URLLoader(url, **kwargs)
    loader.load()
    return loader

load_url = from_url


def from_directory(directory, index_file=None, **kwargs):
    from .loaders import DirectoryLoader
    loader = DirectoryLoader(directory, index_file=index_file, **kwargs)
    loader.load()
    return loader

def from_file(filename, **kwargs):
    return from_directory(directory=os.path.dirname(filename), index_file=os.path.basename(filename), **kwargs)


def from_zip(zip_file, **kwargs):
    from .loaders import ZipLoader
    loader = ZipLoader(zip_file, **kwargs)
    loader.load()
    return loader


def from_string(html, css_text=None, **kwargs):
    from .loaders import StringLoader
    loader = StringLoader(html, css_text=css_text, **kwargs)
    loader.load()
    return loader

