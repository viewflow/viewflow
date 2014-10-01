#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='django-viewflow',
    version='0.6.0',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    description='Activity based reusable workflow library for django',
    long_description=open('README.rst').read(),
    license='AGPLv3',
    platforms=['Any'],
    keywords=['workflow', 'django', 'bpm', 'automaton'],
    url='http://github.com/kmmbvnr/django-viewflow',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        # viewflow
        'Django>=1.6',
        'singledispatch>=3.0',
        'django-fsm>=2.0',
        # viewflow.site
        'django-extra-views',
        'django-tag-parser>=2.0b1',
        'django-formset-js',
        'django-braces',
        'docutils',
        # viewflow.test
        'django-webtest',
        'webtest'
    ],
    packages=['viewflow',
              'viewflow.contrib',
              'viewflow.flow',
              'viewflow.management',
              'viewflow.migrations',
              'viewflow.south_migrations',
              'viewflow.templatetags',
              'viewflow.site',
              'viewflow.site.templatetags',
              'viewflow.views'],
    include_package_data=True)
