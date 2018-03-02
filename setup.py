# -*- coding: utf-8 -*-
import os
from setuptools import find_packages, setup

dir = os.path.dirname(__file__)

reqs = open(os.path.join(dir, 'requirements.txt')).read()

required = reqs.split()


setup(
    name='cassettedeck',
    version='1.0',
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
    install_requires=required
)