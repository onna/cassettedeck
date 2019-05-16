# -*- coding: utf-8 -*-
from setuptools import find_packages, setup


setup(
    name='cassettedeck',
    version='2.0.2',
    description='A library store and replay aiohttp requests',
    long_description='To simplify and speed up tests that make HTTP requests',
    author='Developer team at Onna Technologies',
    author_email='dev@onna.com',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    url='http://github.com/onna/cassettedeck',
    license='Public',
    zip_safe=True,
    include_package_data=True,
    package_data={'': ['*.txt', '*.rst']},
    packages=find_packages(),
    install_requires=[
        'aiohttp>=3.4,<3.6',
        'vcrpy==1.12.0',
        'PyYAML~=3.12.0'
    ]
)
