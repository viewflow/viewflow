import setuptools


setuptools.setup(
    name='django-viewflow',
    version='2.0.0a3',
    author_email='kmmbvnr@gmail.com',
    author='Mikhail Podgurskiy',
    description="Reusable library to build business applications fast",
    include_package_data=True,
    keywords=['django', 'admin', 'workflow', 'fsm', 'bpm', 'bpmn'],
    license='AGPL',
    long_description_content_type="text/markdown",
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    packages=setuptools.find_packages(exclude=['tests*']),
    python_requires='>=3.7',
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Framework :: Django :: 3.1',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
    ],
    install_requires=[
        'Django>=3.2',
        'django-filter>=2.3.0',
    ],
)
