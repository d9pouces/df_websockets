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
"""load Celery and discover tasks
==============================

You should not use this module (or rename it), as it is only used to auto-discover tasks.

"""

import logging.config

from celery import Celery, signals
from django.apps import apps
from django.conf import settings

from df_config.manage import set_env

module_name = set_env()
app = Celery(module_name)
app.config_from_object(settings)

app.autodiscover_tasks([a.name for a in apps.app_configs.values()])


# noinspection PyUnusedLocal
@signals.setup_logging.connect
def setup_celery_logging(**kwargs):
    """Use to setup the logs, overriding the default Celery configuration """
    logging.config.dictConfig(settings.LOGGING)


# Moving the call here works
app.log.setup()
