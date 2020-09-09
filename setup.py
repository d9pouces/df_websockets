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

from setuptools import setup

setup(
    test_suite="test_df_websockets",
    install_requires=[
        "asgiref",
        "celery",
        "channels",
        "channels_redis",
        "df_config",
        "django",
        "pyasn1>=0.4.8",
        "redis",
    ],
    setup_requires=[],
    tests_require=["tox"],
)
