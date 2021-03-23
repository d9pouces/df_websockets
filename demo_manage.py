#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from django.core.management import execute_from_command_line


def main():
    os.environ["DJANGO_SETTINGS_MODULE"] = "demo_df_websockets.settings"
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
