#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup


setup(
    name='django-viewflow',
    version='0.1.0',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    description='Task based reusable workflow library for django',
    license='GPLv3',
    platforms=['Any'],
    keywords=['workflow', 'django'],
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
    requires=['Django (>=1.7b1)', 'celery (>=3.1)'],
    packages=['viewflow', 'viewflow.flow', 'viewflow.templatetags'],
    package_data={'viewflow': ['templates/viewflow/*.html', 'templates/viewflow/flow/*.html']},
)
