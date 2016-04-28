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
    'djangorestframework',
]


docs_extras = [
]

tests_require = [
]

testing_extras = tests_require + [
]


class MyTest(TestCommand):
    def run_tests(self):
        import os
        if "DJANGO_SETTINGS_MODULE" not in os.environ:
            os.environ["DJANGO_SETTINGS_MODULE"] = "django_returnfields.tests.settings"
        from django.test.utils import get_runner
        import django
        from django.apps import apps
        django.setup()
        for config in apps.get_app_configs():
            config.models_module = __name__
        from django.conf import settings
        factory = get_runner(settings)
        test_runner = factory()
        return test_runner.run_tests(["django_returnfields.tests"])


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
      test_suite="django_returnfields.tests",  # dummy
      cmdclass={"test": MyTest},
      entry_points="""
""")
