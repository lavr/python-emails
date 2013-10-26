# encoding: utf-8
import os, os.path
import logging
from .htmlloader import HTTPLoader
from .fileloader import FileSystemLoader, ZipLoader
from .stylesheets import PageStylesheets


def from_url(url, **kwargs):
    loader = HTTPLoader()
    loader.load_url(url=url, **kwargs)
    return loader

load_url = from_url

def from_file(filename, **kwargs):
    return from_directory(directory=os.path.dirname(filename), index_file=os.path.basename(filename), **kwargs)

def from_directory(directory, index_file=None, **kwargs):
    loader = HTTPLoader()
    local_loader = FileSystemLoader(searchpath=directory)
    index_file_name = local_loader.find_index_file(index_file)
    dirname, basename = os.path.split(index_file_name)
    if dirname:
        local_loader.base_path = dirname
    loader.load_file(local_loader[basename], local_loader=local_loader,  **kwargs)
    return loader

def from_zip(zip_file, **kwargs):
    loader = HTTPLoader()
    local_store = ZipLoader(file=zip_file)
    index_file_name = local_store.find_index_file()
    dirname, basename = os.path.split(index_file_name)
    if dirname:
        local_store.base_path = dirname
    logging.debug('from_zip: found index file: %s', index_file_name)
    loader.load_file(local_store[basename], local_loader=local_store,  **kwargs)
    return loader

def from_string(html, css=None, **kwargs):
    loader = HTTPLoader()
    loader.load_string(html=html, css=css,  **kwargs)
    return loader

