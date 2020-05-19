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
from django.conf import settings
from django.core.management import BaseCommand

from df_websockets import ws_settings

try:
    from django.utils.autoreload import python_reloader

    run_with_reloader = None
except ImportError:
    python_reloader = None
    from django.utils.autoreload import run_with_reloader


class Command(BaseCommand):
    """run the "celery" "worker" command."""

    help = "Manage queue workers"

    def run_from_argv(self, argv):
        os.environ.setdefault("CELERY_APP", ws_settings.CELERY_APP)
        if settings.DEBUG and "-h" not in sys.argv:
            if "-c" not in sys.argv and "--pool" not in sys.argv and "-P" not in sys.argv and "--concurrency" not in sys.argv:
                sys.argv += ["-c", "1", "--pool", "solo"]
            if callable(run_with_reloader):
                run_with_reloader(celery_main, sys.argv)
            elif callable(python_reloader):
                python_reloader(celery_main, (sys.argv,), {})
        else:
            celery_main(sys.argv)

    def handle(self, *args, **options):
        pass
