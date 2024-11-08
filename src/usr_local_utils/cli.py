import logging
import logging.config

import click

from .supported_apps import Bat, Eza, FdFind, Fzf, Ripgrep, Starship


class AppNameContext(logging.Filter):
    def filter(self, record):
        if not getattr(record, "app_name", None):
            record.app_name = "installer"
        return True


_CLI_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {"app_name_context": {"()": AppNameContext}},
    "formatters": {
        "logfmt": {"format": "lvl=%(levelname)s app=%(app_name)s msg=%(message)s"}
    },
    "handlers": {
        "console": {
            "filters": ["app_name_context"],
            "formatter": "logfmt",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # root logger
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "usr_local_utils": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


@click.command()
def cli():
    """Example script."""
    logging.config.dictConfig(_CLI_LOGGING_CONFIG)

    # prefix = "/usr/local"
    prefix = "/tmp/installer_simulate"

    logging.info("Installing into: %s", prefix)

    installed = []

    for app in [
        Bat(prefix=prefix),
        Eza(prefix=prefix),
        FdFind(prefix=prefix),
        Fzf(prefix=prefix),
        Starship(prefix=prefix),
        Ripgrep(prefix=prefix),
    ]:
        installed.extend(app.install())

    if installed:
        print("Installed files:")
        for _ in installed:
            print(f"- {_}")
