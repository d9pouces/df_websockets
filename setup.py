# ##############################################################################
#  This file is part of df_websockets                                          #
#                                                                              #
#  Copyright (C) 2020 Matthieu Gallet <github@19pouces.net>                    #
#  All Rights Reserved                                                         #
#                                                                              #
#  You may use, distribute and modify this code under the                      #
#  terms of the (BSD-like) CeCILL-B license.                                   #
#                                                                              #
#  You should have received a copy of the CeCILL-B license with                #
#  this file. If not, please visit:                                            #
#  https://cecill.info/licences/Licence_CeCILL-B_V1-en.txt (English)           #
#  or https://cecill.info/licences/Licence_CeCILL-B_V1-fr.txt (French)         #
#                                                                              #
# ##############################################################################

import os.path
import re

from setuptools import find_packages, setup

# avoid a from df_websockets import __version__ as version (that compiles df_websockets.__init__ and is not compatible with bdist_deb)
version = None
for line in open(os.path.join("df_websockets", "__init__.py"), "r"):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)

# get README content from README.md file
with open(os.path.join(os.path.dirname(__file__), "README.md")) as fd:
    long_description = fd.read()

setup(
    name="df_websockets",
    version=version,
    description="Smart default settings for Django websites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Matthieu Gallet",
    author_email="github@19pouces.net",
    license="CeCILL-B",
    url="https://github.com/d9pouces/df_websockets",
    entry_points={},
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite="test_df_websockets",
    install_requires=[
        "asgiref",
        "celery",
        "channels",
        "channels_redis",
        "django",
        "redis",
    ],
    setup_requires=[],
    tests_require=["tox"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
    ],
)
