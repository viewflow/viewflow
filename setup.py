#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name = 'django-viewflow',
    version = '0.0.1',
    author = 'Mikhail Podgurskiy',
    author_email = 'kmmbvnr@gmail.com',
    description = 'Explicitify django views flow',
    license = 'BSD',
    platforms = ['Any'],
    keywords = ['workflow', 'django'],
    url = 'http://github.com/kmmbvnr/django-viewflow',
    classifiers = [
        'Development Status :: Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=['Django>=1.6b1'],
    packages = ['viewflow'],
    zip_safe = False,
    include_package_data=True
)

