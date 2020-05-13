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
import os
import sys

from celery.bin.celery import main as celery_main
from django.core.management import BaseCommand

from df_websockets import ws_settings


class Command(BaseCommand):
    """run celery commands"""

    help = "Manage workers and inspect queues"

    def run_from_argv(self, argv):
        os.environ.setdefault("CELERY_APP", ws_settings.CELERY_APP)
        sys.argv.pop(0)
        celery_main(sys.argv)

    def handle(self, *args, **options):
        pass
