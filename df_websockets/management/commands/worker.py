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
import logging
import os
import sys

from channels.layers import get_channel_layer
from channels.management.commands.runworker import Command as BaseCommand
from channels.routing import get_default_application
from django.conf import settings
from django.core.management import CommandError
from django.utils.autoreload import run_with_reloader

from df_websockets import ws_settings
from df_websockets.constants import WORKER_CELERY

logger = logging.getLogger("django.channels.worker")


class Command(BaseCommand):
    """run the "celery" "worker" command."""

    help = "Manage queue workers"

    def run_from_argv(self, argv):
        if ws_settings.WEBSOCKET_WORKERS == WORKER_CELERY:
            from celery.bin.celery import main as celery_main

            os.environ.setdefault("CELERY_APP", ws_settings.CELERY_APP)
            if settings.DEBUG and "-h" not in sys.argv:
                if not any(
                    x in sys.argv for x in ("-c", "--concurrency", "-P", "--pool")
                ):
                    sys.argv += ["-c", "1", "--pool", "solo"]
                return run_with_reloader(celery_main)
            celery_main()
        super().run_from_argv(argv)

    def add_arguments(self, parser):
        super(BaseCommand, self).add_arguments(parser)
        parser.add_argument("-Q", "--queues", help="Queue Options")

    def handle(self, *args, **options):
        # Get the backend to use
        # noinspection PyAttributeOutsideInit
        self.verbosity = options.get("verbosity", 1)
        queues_str = options.get("queues")
        if queues_str:
            queues = [x.strip() for x in options["queues"].split(",") if x.strip()]
        else:
            queues = [ws_settings.WEBSOCKET_DEFAULT_QUEUE]
        # Get the channel layer they asked for (or see if one isn't configured)
        channel_layer = get_channel_layer()
        if channel_layer is None:
            raise CommandError("You do not have any CHANNEL_LAYERS configured.")
        # Run the worker
        logger.info("Running worker for channels %s", ", ".join(queues))
        worker = self.worker_class(
            application=get_default_application(),
            channels=queues,
            channel_layer=channel_layer,
        )
        worker.run()
