# coding=utf8

"""
Gmls
----

GitHub Markdown Local Server.

Install
````````

.. code:: bash

    $ [sudo] pip install gmls

Source
```````
* GitHub <https://github.com/hit9/gmls>

"""

import re
import ast
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('gmls/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')
    ).group(1)))

setup(
    name='gmls',
    version=version,
    author_email='hit9@icloud.com',
    description='GitHub Markdown Local Server.',
    license='MIT',
    keywords='github markdown local server',
    url='http://github.com/hit9/gmls',
    packages=['gmls'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': ['gmls=gmls:main']
    },
    install_requires=[
        'binaryornot==0.3.0',
        'docopt==0.6.2',
        'Flask==0.10.1',
        'houdini.py==0.1.0',
        'misaka==1.0.2',
        'pygments==2.0.2'
    ],
    long_description=__doc__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Customer Service',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ]
)
