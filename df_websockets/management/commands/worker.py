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

# noinspection PyPackageRequirements
from celery.bin.celery import main as celery_main
# noinspection PyPackageRequirements
from django.conf import settings
# noinspection PyPackageRequirements
from django.core.management import BaseCommand
# noinspection PyPackageRequirements
from django.utils.autoreload import run_with_reloader

from df_websockets import ws_settings


class Command(BaseCommand):
    """run the "celery" "worker" command."""

    help = "Manage queue workers"

    def run_from_argv(self, argv):
        os.environ.setdefault("CELERY_APP", ws_settings.CELERY_APP)
        if settings.DEBUG and "-h" not in sys.argv:
            if not any(x in sys.argv for x in ("-c", "--concurrency", "-P", "--pool")):
                sys.argv += ["-c", "1", "--pool", "solo"]
            return run_with_reloader(celery_main)
        celery_main()

    def handle(self, *args, **options):
        pass
