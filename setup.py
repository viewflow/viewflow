#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='django-viewflow',
    version='0.12.0',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    description='Reusable workflow library for django',
    long_description=open('README.rst').read(),
    license='AGPLv3',
    platforms=['Any'],
    keywords=['workflow', 'django', 'bpm', 'automaton'],
    url='http://github.com/viewflow/viewflow',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        # viewflow
        'Django>=1.8',
        'django-fsm>=2.0',
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
