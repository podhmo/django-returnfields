# -*- coding:utf-8 -*-

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''


install_requires = [
    'django >= 1.9',
    'djangorestframework',
    'django-aggressivequery'
]


docs_extras = [
]

tests_require = [
]

testing_extras = tests_require + [
    "tox"
]


class MyTest(TestCommand):
    # if you want to run specific tests only.
    # `python setup.py test -s  django_returnfields.tests.<module>.<class>.<method>`

    user_options = TestCommand.user_options + [
        ('logging=', 'l', "logging"),
    ]

    def initialize_options(self):
        self.logging = None
        super(MyTest, self).initialize_options()

    def finalize_options(self):
        super(MyTest, self).finalize_options()
        if self.logging is not None:
            import logging
            logging.basicConfig(level=getattr(logging, self.logging.upper(), 0))

    def run_tests(self):
        import os
        if "DJANGO_SETTINGS_MODULE" not in os.environ:
            os.environ["DJANGO_SETTINGS_MODULE"] = "django_returnfields.tests.settings"
        from django.test.utils import get_runner
        from django.conf import settings
        import django
        django.setup()
        sys.exit(get_runner(settings)().run_tests([self.test_args[-1]]))


setup(name='django-returnfields',
      version='0.3.2',
      description='adding restriction of your api\'s return fields, in restframework',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: 3 :: Only",
          'Framework :: Django',
          'License :: OSI Approved :: BSD License',
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
      cmdclass={"test": MyTest},
      entry_points="""
""")
