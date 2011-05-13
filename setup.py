#!/usr/bin/env python
# usage: python setup.py install

from distutils.core import setup
import os

setup(
  name='tix',
  version='0.0-pre-alpha',
  #data_files=[ (os.path.join(os.getenv('USERPROFILE') or os.getenv('HOME'), 'tix', 'docs'), ['docs/README.txt']), ],
  py_modules=[
    'tix.curses_main',
    'tix.utils',
    'tix.note',
    'tix.control',
    'tix.curses_view',
    'tix.gtk_main',
    'tix.gtk_undobuffer',
    'tix.gtk_classes',
  ],
  scripts=['tix/tix'],
  requires=['gtk', 'curses'],
  description='TIX text file manager',
  author='Sina Siadatnejad',
  author_email='siadat@gmail.com',
  license='MIT',
)
