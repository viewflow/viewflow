#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='django-viewflow',
    version='1.0.1',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    description='Reusable workflow library for django',
    long_description=open('README.rst').read(),
    platforms=['Any'],
    keywords=['workflow', 'django', 'bpm', 'automaton'],
    url='http://github.com/viewflow/viewflow',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
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
