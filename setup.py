import setuptools

README = open("README.md", "r", encoding="utf-8").read()

setuptools.setup(
    name="django-viewflow",
    version="2.2.9",
    author_email="kmmbvnr@gmail.com",
    author="Mikhail Podgurskiy",
    description="Reusable library to build business applications fast",
    include_package_data=True,
    keywords=["django", "admin", "workflow", "fsm", "bpm", "bpmn"],
    license="AGPL",
    # long_description_content_type="text/markdown",
    # long_description=README,
    long_description_content_type="text/markdown",
    long_description=README,
    packages=setuptools.find_packages(exclude=["tests*"]),
    python_requires=">=3.8",
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
    ],
    install_requires=[
        "Django>=4.2",
        "django-filter>=2.3.0",
    ],
)
