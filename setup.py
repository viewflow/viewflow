#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='django-viewflow',
    version='0.2.0',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    description='Activity based reusable workflow library for django',
    long_description=open('README.rst').read(),
    license='AGPLv3',
    platforms=['Any'],
    keywords=['workflow', 'django', 'bpm'],
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
    install_requires=['Django>=1.6',
                      'celery>=3.1',
                      'singledispatch>=3.4',
                      'django-fsm>=2.0',
                      'webtest>=2.0',
                      'django-webtest>=1.7'],
    packages=['viewflow', 'viewflow.flow', 'viewflow.management', 'viewflow.templatetags'],
    package_data={'viewflow': ['templates/viewflow/*.html', 'templates/viewflow/flow/*.html']},
)
