#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='django-viewflow-pro',
    version='0.12.2.1',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    description='Reusable workflow library for django',
    long_description=open('README.rst').read(),
    platforms=['Any'],
    keywords=['workflow', 'django', 'bpm', 'automaton'],
    url='http://github.com/viewflow/viewflow',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'Django>=1.8',
        'django-filter>=1.0'
    ],
    packages=['viewflow',
              'viewflow.flow',
              'viewflow.flow.views',
              'viewflow.management',
              'viewflow.migrations',
              'viewflow.nodes',
              'viewflow.templatetags',
              'viewflow.frontend',
              'viewflow.frontend.templatetags'],
    include_package_data=True,
    zip_safe=False)
