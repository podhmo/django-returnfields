# -*- coding:utf-8 -*-

import os
import sys


from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''


install_requires = [
    'djangorestframework',
]


docs_extras = [
]

tests_require = [
]

testing_extras = tests_require + [
]

setup(name='django-returnfields',
      version='0.0',
      description='adding restriction of your api\'s return fields, in restframework',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: Implementation :: CPython",
      ],
      keywords='django restframework return_fields',
      author="podhmo",
      author_email="",
      url="https://github.com/podhmo/django-returnfields",
      packages=find_packages(exclude=["django_returnfields.tests"]),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require={
          'testing': testing_extras,
          'docs': docs_extras,
      },
      tests_require=tests_require,
      test_suite="django_returnfields.tests",
      entry_points="""
""")
